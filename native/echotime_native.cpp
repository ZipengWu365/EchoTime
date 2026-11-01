// Native kernels for EchoTime's elastic distances and sample entropy.
//
// Every kernel reproduces the arithmetic of the pure-Python reference in
// src/echotime/similarity_methods.py and src/echotime/metrics.py operation by
// operation (same operands, same order, IEEE double, no fast-math, no FMA
// contraction), so results are bit-identical to the reference. Per-series
// quantities (gap costs, TWED delete costs, previous rows, timestamps) are
// computed in Python with the reference helpers and passed in.
//
// Series are stored in "banks": a C-contiguous (rows, d) value array plus an
// int64 offsets array of length S+1; series s occupies rows off[s]..off[s+1].
// Pair kernels take index arrays I (into bank A) and J (into bank B) and run
// pairs in parallel with std::thread (no OpenMP runtime needed, so the same
// code builds on Linux, macOS and Windows). The GIL is released while
// kernels run.

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <thread>
#include <vector>

namespace py = pybind11;

using arr_d = py::array_t<double, py::array::c_style | py::array::forcecast>;
using arr_i = py::array_t<int64_t, py::array::c_style | py::array::forcecast>;

namespace {

constexpr double kInf = std::numeric_limits<double>::infinity();
constexpr double kNaN = std::numeric_limits<double>::quiet_NaN();
constexpr double kFastBandRatio = 0.10;  // similarity_methods._FAST_MODE_BAND_RATIO

struct Bank {
  const double* v = nullptr;
  const int64_t* off = nullptr;
  int64_t d = 1;
  int64_t S = 0;
  int64_t len(int64_t s) const { return off[s + 1] - off[s]; }
  const double* row(int64_t s, int64_t i) const { return v + (off[s] + i) * d; }
};

// A per-row scalar array aligned with a bank's rows (gap costs, delete costs,
// timestamps). Indexed with the same offsets as the bank.
struct RowScalars {
  const double* v = nullptr;
  const int64_t* off = nullptr;
  const double* at(int64_t s) const { return v + off[s]; }
};

Bank make_bank(const arr_d& values, const arr_i& offsets) {
  if (values.ndim() != 2) throw std::invalid_argument("values must be 2-D (rows, d)");
  if (offsets.ndim() != 1 || offsets.shape(0) < 1) throw std::invalid_argument("offsets must be 1-D with length S+1");
  Bank b;
  b.v = values.data();
  b.off = offsets.data();
  b.d = values.shape(1);
  b.S = offsets.shape(0) - 1;
  if (b.off[0] != 0 || b.off[b.S] != values.shape(0)) throw std::invalid_argument("offsets do not match values rows");
  for (int64_t s = 0; s < b.S; ++s)
    if (b.off[s + 1] < b.off[s]) throw std::invalid_argument("offsets must be nondecreasing");
  return b;
}

RowScalars make_rows(const arr_d& values, const Bank& bank, const char* name) {
  if (values.ndim() != 1 || values.shape(0) != bank.off[bank.S])
    throw std::invalid_argument(std::string(name) + " must be 1-D with one value per bank row");
  RowScalars r;
  r.v = values.data();
  r.off = bank.off;
  return r;
}

void check_pairs(const arr_i& I, const arr_i& J, const Bank& A, const Bank& B) {
  if (I.ndim() != 1 || J.ndim() != 1 || I.shape(0) != J.shape(0)) throw std::invalid_argument("I and J must be 1-D of equal length");
  const int64_t* pi = I.data();
  const int64_t* pj = J.data();
  for (int64_t k = 0; k < I.shape(0); ++k) {
    if (pi[k] < 0 || pi[k] >= A.S || pj[k] < 0 || pj[k] >= B.S) throw std::out_of_range("pair index out of range");
  }
  if (A.d != B.d) throw std::invalid_argument("banks must have the same channel count");
}

// numpy's pairwise summation (pairwise_sum_DOUBLE, PW_BLOCKSIZE = 128), which
// np.sum(..., axis=1) uses for each row of a C-contiguous (k, d) array.
double pairwise_sum(const double* a, int64_t n) {
  if (n < 8) {
    double res = 0.0;
    for (int64_t i = 0; i < n; ++i) res += a[i];
    return res;
  }
  if (n <= 128) {
    double r[8];
    for (int k = 0; k < 8; ++k) r[k] = a[k];
    int64_t i = 8;
    for (; i < n - (n % 8); i += 8)
      for (int k = 0; k < 8; ++k) r[k] += a[i + k];
    double res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
    for (; i < n; ++i) res += a[i];
    return res;
  }
  int64_t n2 = n / 2;
  n2 -= n2 % 8;
  return pairwise_sum(a, n2) + pairwise_sum(a + n2, n - n2);
}

// sum((b - a)**2) exactly as np.sum(diff * diff, axis=1) with diff = b - a.
inline double squared_l2(const double* a, const double* b, int64_t d, double* buf) {
  for (int64_t k = 0; k < d; ++k) {
    const double diff = b[k] - a[k];
    buf[k] = diff * diff;
  }
  return pairwise_sum(buf, d);
}

// _row_l2_distances(row=a, candidates=b): |b - a| for d == 1, else sqrt of the
// pairwise sum of squares.
inline double l2(const double* a, const double* b, int64_t d, double* buf) {
  if (d == 1) return std::fabs(b[0] - a[0]);
  return std::sqrt(squared_l2(a, b, d, buf));
}

// _row_match_mask: |b - a| <= eps for d == 1, else sum((b-a)^2) <= eps*eps.
inline bool match(const double* a, const double* b, int64_t d, double eps, double eps2, double* buf) {
  if (d == 1) return std::fabs(b[0] - a[0]) <= eps;
  return squared_l2(a, b, d, buf) <= eps2;
}

// _resolved_window: -1 means "no band".
inline int64_t resolve_window(int64_t n, int64_t m, int64_t window, bool fast) {
  int64_t w;
  if (window < 0) {
    if (!fast) return -1;
    w = static_cast<int64_t>(std::ceil(kFastBandRatio * static_cast<double>(std::max(n, m))));
  } else {
    w = window;
  }
  const int64_t diff = n > m ? n - m : m - n;
  return std::max(w, diff);
}

// _window_bounds: j in [lo, hi] inclusive (1-based).
inline void window_bounds(int64_t i, int64_t m, int64_t w, int64_t& lo, int64_t& hi) {
  if (w < 0) {
    lo = 1;
    hi = m;
  } else {
    lo = std::max<int64_t>(1, i - w);
    hi = std::min<int64_t>(m, i + w);
  }
}

int resolve_threads(int n_threads, int64_t n_items) {
  int t = n_threads;
  if (t <= 0) {
    const unsigned hc = std::thread::hardware_concurrency();
    t = hc == 0 ? 1 : static_cast<int>(hc);
  }
  if (static_cast<int64_t>(t) > n_items) t = static_cast<int>(std::max<int64_t>(1, n_items));
  return t;
}

// Dynamic scheduling over items; f(item, thread_id).
template <class F>
void parallel_for(int64_t n_items, int n_threads, F&& f) {
  const int t = resolve_threads(n_threads, n_items);
  if (t <= 1) {
    for (int64_t k = 0; k < n_items; ++k) f(k, 0);
    return;
  }
  std::atomic<int64_t> next(0);
  auto worker = [&](int tid) {
    for (;;) {
      const int64_t k = next.fetch_add(1, std::memory_order_relaxed);
      if (k >= n_items) break;
      f(k, tid);
    }
  };
  std::vector<std::thread> pool;
  pool.reserve(static_cast<size_t>(t - 1));
  for (int tid = 1; tid < t; ++tid) pool.emplace_back(worker, tid);
  worker(0);
  for (auto& th : pool) th.join();
}

// The dynamic programmes are templated on UNI (d == 1). The univariate
// instantiation indexes raw pointers with a compile-time stride of one and
// uses |b - a| directly; the multichannel one goes through l2()/match(). Both
// perform the reference's arithmetic in the reference's order.
//
// Cells outside a Sakoe-Chiba band must hold the reference's fill value
// (0 for LCSS, +inf otherwise); only those ranges are reset per row.

template <bool UNI>
inline double cost_l2(const double* a, const double* b, int64_t d, double* buf) {
  if constexpr (UNI) {
    return std::fabs(b[0] - a[0]);
  } else {
    return l2(a, b, d, buf);
  }
}

template <bool UNI>
inline bool cost_match(const double* a, const double* b, int64_t d, double eps, double eps2, double* buf) {
  if constexpr (UNI) {
    return std::fabs(b[0] - a[0]) <= eps;
  } else {
    return match(a, b, d, eps, eps2, buf);
  }
}

// The reference refills the whole row before every banded row (O(m) per row,
// which would cancel the band's O(n*w) cost). Equivalent cheaper rule:
// - rows 1 and 2 reset every cell outside the band (this also clears the
//   row-0 initialisation of EDR/ERP from the second buffer);
// - from row 3 the band only moves right, so cells right of it still hold the
//   fill value and the only stale cell that is ever read is lo-1 (as
//   curr[j-1] at j = lo); reset just that one. Stale cells further left are
//   never read again. Cell 0 is the boundary and is set by each kernel.
inline void reset_outside(std::vector<double>& row, int64_t i, int64_t lo, int64_t hi, int64_t m, double fill) {
  double* r = row.data();
  if (i <= 2) {
    for (int64_t j = 1; j < lo; ++j) r[j] = fill;
    for (int64_t j = hi + 1; j <= m; ++j) r[j] = fill;
  } else if (lo >= 2) {
    r[lo - 1] = fill;
  }
}

inline double min3(double a, double b, double c) {
  // Python min(a, b, c): first minimum. Values are never NaN here.
  double r = a;
  if (b < r) r = b;
  if (c < r) r = c;
  return r;
}

// ---------------------------------------------------------------- LCSS ----
template <bool UNI>
double lcss_one(const Bank& A, int64_t sa, const Bank& B, int64_t sb, double eps, int64_t window, bool fast,
                std::vector<double>& prev, std::vector<double>& curr, std::vector<double>& buf) {
  const int64_t n = A.len(sa), m = B.len(sb), d = UNI ? 1 : A.d;
  if (n == 0 || m == 0) return kNaN;
  const int64_t w = resolve_window(n, m, window, fast);
  const double eps2 = eps * eps;
  const double* xa = A.row(sa, 0);
  const double* yb = B.row(sb, 0);
  prev.assign(static_cast<size_t>(m + 1), 0.0);
  curr.assign(static_cast<size_t>(m + 1), 0.0);
  buf.resize(static_cast<size_t>(d));
  for (int64_t i = 1; i <= n; ++i) {
    int64_t lo, hi;
    window_bounds(i, m, w, lo, hi);
    double* c = curr.data();
    const double* p = prev.data();
    c[0] = 0.0;
    if (w >= 0) reset_outside(curr, i, lo, hi, m, 0.0);
    const double* a = xa + (i - 1) * d;
    for (int64_t j = lo; j <= hi; ++j) {
      if (cost_match<UNI>(a, yb + (j - 1) * d, d, eps, eps2, buf.data())) {
        c[j] = p[j - 1] + 1.0;
      } else {
        // Python max(prev[j], curr[j - 1]): equal values are identical, so
        // only the value matters.
        c[j] = (c[j - 1] > p[j]) ? c[j - 1] : p[j];
      }
    }
    std::swap(prev, curr);
  }
  return prev[static_cast<size_t>(m)] / static_cast<double>(std::max<int64_t>(1, std::min(n, m)));
}

// ----------------------------------------------------------------- EDR ----
template <bool UNI>
double edr_one(const Bank& A, int64_t sa, const Bank& B, int64_t sb, double eps, bool normalized, int64_t window,
               bool fast, std::vector<double>& prev, std::vector<double>& curr, std::vector<double>& buf) {
  const int64_t n = A.len(sa), m = B.len(sb), d = UNI ? 1 : A.d;
  if (n == 0 || m == 0) return kNaN;
  const int64_t w = resolve_window(n, m, window, fast);
  const double eps2 = eps * eps;
  const double* xa = A.row(sa, 0);
  const double* yb = B.row(sb, 0);
  prev.resize(static_cast<size_t>(m + 1));
  curr.assign(static_cast<size_t>(m + 1), kInf);
  for (int64_t j = 0; j <= m; ++j) prev[j] = static_cast<double>(j);
  buf.resize(static_cast<size_t>(d));
  for (int64_t i = 1; i <= n; ++i) {
    int64_t lo, hi;
    window_bounds(i, m, w, lo, hi);
    double* c = curr.data();
    const double* p = prev.data();
    c[0] = static_cast<double>(i);
    if (w >= 0) reset_outside(curr, i, lo, hi, m, kInf);
    const double* a = xa + (i - 1) * d;
    for (int64_t j = lo; j <= hi; ++j) {
      const double sub = cost_match<UNI>(a, yb + (j - 1) * d, d, eps, eps2, buf.data()) ? 0.0 : 1.0;
      c[j] = min3(p[j] + 1.0, c[j - 1] + 1.0, p[j - 1] + sub);
    }
    std::swap(prev, curr);
  }
  double value = prev[static_cast<size_t>(m)];
  if (normalized) value /= static_cast<double>(std::max<int64_t>(1, std::max(n, m)));
  return value;
}

// ----------------------------------------------------------------- ERP ----
template <bool UNI>
double erp_one(const Bank& A, int64_t sa, const RowScalars& gapA, const Bank& B, int64_t sb, const RowScalars& gapB,
               int64_t window, bool fast, std::vector<double>& prev, std::vector<double>& curr,
               std::vector<double>& buf) {
  const int64_t n = A.len(sa), m = B.len(sb), d = UNI ? 1 : A.d;
  if (n == 0 || m == 0) return kNaN;
  const int64_t w = resolve_window(n, m, window, fast);
  const double* lg = gapA.at(sa);
  const double* rg = gapB.at(sb);
  const double* xa = A.row(sa, 0);
  const double* yb = B.row(sb, 0);
  prev.assign(static_cast<size_t>(m + 1), kInf);
  curr.assign(static_cast<size_t>(m + 1), kInf);
  buf.resize(static_cast<size_t>(d));
  prev[0] = 0.0;
  for (int64_t j = 1; j <= m; ++j) prev[j] = prev[j - 1] + rg[j - 1];
  for (int64_t i = 1; i <= n; ++i) {
    int64_t lo, hi;
    window_bounds(i, m, w, lo, hi);
    double* c = curr.data();
    const double* p = prev.data();
    const double lgi = lg[i - 1];
    c[0] = p[0] + lgi;
    if (w >= 0) reset_outside(curr, i, lo, hi, m, kInf);
    const double* a = xa + (i - 1) * d;
    for (int64_t j = lo; j <= hi; ++j) {
      const double pair = cost_l2<UNI>(a, yb + (j - 1) * d, d, buf.data());
      c[j] = min3(p[j - 1] + pair, p[j] + lgi, c[j - 1] + rg[j - 1]);
    }
    std::swap(prev, curr);
  }
  return prev[static_cast<size_t>(m)];
}

// ---------------------------------------------------------------- TWED ----
struct TwedSide {
  Bank values;       // cleaned series
  Bank prev_values;  // _previous_rows(values)
  RowScalars t;      // timestamps
  RowScalars tprev;  // previous timestamps (0 for the first row)
  RowScalars del;    // delete costs
};

template <bool UNI>
double twed_one(const TwedSide& L, int64_t sa, const TwedSide& R, int64_t sb, double nu, int64_t window, bool fast,
                std::vector<double>& prev, std::vector<double>& curr, std::vector<double>& buf) {
  const int64_t n = L.values.len(sa), m = R.values.len(sb), d = UNI ? 1 : L.values.d;
  if (n == 0 || m == 0) return kNaN;
  const int64_t w = resolve_window(n, m, window, fast);
  const double* tx = L.t.at(sa);
  const double* txp = L.tprev.at(sa);
  const double* ldel = L.del.at(sa);
  const double* ty = R.t.at(sb);
  const double* typ = R.tprev.at(sb);
  const double* rdel = R.del.at(sb);
  const double* xa = L.values.row(sa, 0);
  const double* xpa = L.prev_values.row(sa, 0);
  const double* yb = R.values.row(sb, 0);
  const double* ypb = R.prev_values.row(sb, 0);
  prev.assign(static_cast<size_t>(m + 1), kInf);
  curr.assign(static_cast<size_t>(m + 1), kInf);
  buf.resize(static_cast<size_t>(d));
  prev[0] = 0.0;
  for (int64_t i = 1; i <= n; ++i) {
    int64_t lo, hi;
    window_bounds(i, m, w, lo, hi);
    double* c = curr.data();
    const double* p = prev.data();
    c[0] = kInf;
    if (w >= 0) reset_outside(curr, i, lo, hi, m, kInf);
    const double* xi = xa + (i - 1) * d;
    const double* xim1 = xpa + (i - 1) * d;
    const double ti = tx[i - 1];
    const double tim1 = txp[i - 1];
    const double ldi = ldel[i - 1];
    for (int64_t j = lo; j <= hi; ++j) {
      const double pair = cost_l2<UNI>(xi, yb + (j - 1) * d, d, buf.data());
      const double pair_prev = cost_l2<UNI>(xim1, ypb + (j - 1) * d, d, buf.data());
      const double time_cost = nu * (std::fabs(ti - ty[j - 1]) + std::fabs(tim1 - typ[j - 1]));
      c[j] = min3(p[j] + ldi, c[j - 1] + rdel[j - 1], p[j - 1] + pair + pair_prev + time_cost);
    }
    std::swap(prev, curr);
  }
  return prev[static_cast<size_t>(m)];
}

// ----------------------------------------------------------------- DTW ----
// Classic DTW: D[i,j] = cost(i,j) + min(D[i-1,j], D[i,j-1], D[i-1,j-1]),
// band |i-j| <= max(window, |n-m|) when a window is given. Returns the raw sum.
template <bool UNI>
double dtw_one(const Bank& A, int64_t sa, const Bank& B, int64_t sb, int64_t window, std::vector<double>& prev,
               std::vector<double>& curr, std::vector<double>& buf) {
  const int64_t n = A.len(sa), m = B.len(sb), d = UNI ? 1 : A.d;
  if (n == 0 || m == 0) return kNaN;
  const int64_t w = resolve_window(n, m, window, false);
  const double* xa = A.row(sa, 0);
  const double* yb = B.row(sb, 0);
  prev.assign(static_cast<size_t>(m + 1), kInf);
  curr.assign(static_cast<size_t>(m + 1), kInf);
  buf.resize(static_cast<size_t>(d));
  prev[0] = 0.0;
  for (int64_t i = 1; i <= n; ++i) {
    int64_t lo, hi;
    window_bounds(i, m, w, lo, hi);
    double* c = curr.data();
    const double* p = prev.data();
    c[0] = kInf;
    if (w >= 0) reset_outside(curr, i, lo, hi, m, kInf);
    const double* a = xa + (i - 1) * d;
    for (int64_t j = lo; j <= hi; ++j) {
      const double cost = cost_l2<UNI>(a, yb + (j - 1) * d, d, buf.data());
      c[j] = cost + min3(p[j], c[j - 1], p[j - 1]);
    }
    std::swap(prev, curr);
  }
  return prev[static_cast<size_t>(m)];
}

// ------------------------------------------------------- lane kernels ----
// For univariate series, pairs with equal lengths (n, m) are evaluated kLanes
// at a time: lane l of every array holds pair l, and the inner loop over
// lanes applies the scalar recurrence to each lane. Lanes never interact, and
// each lane performs exactly the scalar kernel's operations (IEEE add, sub,
// mul, fabs, compare-select; no FMA), so results are bit-identical to the
// scalar kernel while the compiler maps the lane loop onto SIMD registers and
// the kLanes independent dependency chains hide the min-plus latency.
constexpr int kLanes = 8;

// Lane arithmetic. With GCC/Clang, lanes are processed kVW at a time through
// vector extensions (AVX2 registers on x86-64-v3); each operation is the
// IEEE operation the scalar kernel performs, and selects/abs are bitwise, so
// every lane is bit-identical to the scalar kernel. Other compilers use the
// scalar type and the same code.
#if defined(__GNUC__) || defined(__clang__)
typedef double vd __attribute__((vector_size(32)));
typedef long long vi __attribute__((vector_size(32)));
using Lane = vd;
constexpr int kVW = 4;
inline vd vload(const double* p, vd) {
  vd v;
  std::memcpy(&v, p, sizeof(vd));
  return v;
}
inline void vstore(double* p, vd v) { std::memcpy(p, &v, sizeof(vd)); }
inline vd vabs(vd v) {
  const vi mask = {0x7fffffffffffffffLL, 0x7fffffffffffffffLL, 0x7fffffffffffffffLL, 0x7fffffffffffffffLL};
  return (vd)((vi)v & mask);
}
inline vd vsel(vi m, vd a, vd b) { return (vd)(((vi)a & m) | ((vi)b & ~m)); }
inline vd vmin_first(vd r, vd b) { return vsel((vi)(b < r), b, r); }  // (b < r) ? b : r
inline vd vle_zero_one(vd a, double eps) {                              // (a <= eps) ? 0.0 : 1.0
  const vd one = {1.0, 1.0, 1.0, 1.0};
  return vsel((vi)(a <= eps), vd{0.0, 0.0, 0.0, 0.0}, one);
}
inline vd vlcss(vd pj1, vd cj1, vd pj, vd ad, double eps) {
  const vd keep = vsel((vi)(cj1 > pj), cj1, pj);
  return vsel((vi)(ad <= eps), pj1 + 1.0, keep);
}
#else
using Lane = double;
constexpr int kVW = 1;
#endif
inline double vload(const double* p, double) { return *p; }
inline void vstore(double* p, double v) { *p = v; }
inline double vabs(double v) { return std::fabs(v); }
inline double vmin_first(double r, double b) { return (b < r) ? b : r; }
inline double vle_zero_one(double a, double eps) { return (a <= eps) ? 0.0 : 1.0; }
inline double vlcss(double pj1, double cj1, double pj, double ad, double eps) {
  const double keep = (cj1 > pj) ? cj1 : pj;
  return (ad <= eps) ? pj1 + 1.0 : keep;
}
#define LD(ptr) vload((ptr) + h, Lane{})

struct Scratch {
  std::vector<double> prev, curr, buf;          // scalar kernels
  std::vector<double> lp, lc;                   // lane rows (m+1)*kLanes
  std::vector<double> xa, xb, xpa, xpb, ta, tb, tpa, tpb, da, db;  // packed inputs
};

inline void pack(std::vector<double>& dst, const double* const* src, int64_t len) {
  dst.resize(static_cast<size_t>(len * kLanes));
  double* d = dst.data();
  for (int64_t i = 0; i < len; ++i)
    for (int l = 0; l < kLanes; ++l) d[i * kLanes + l] = src[l][i];
}

inline void lane_fill(double* row, int64_t from, int64_t to, double value) {
  for (int64_t j = from; j <= to; ++j)
    for (int l = 0; l < kLanes; ++l) row[j * kLanes + l] = value;
}

inline void lane_reset_outside(double* row, int64_t i, int64_t lo, int64_t hi, int64_t m, double fill) {
  // Same rule as reset_outside, for every lane.
  if (i <= 2) {
    lane_fill(row, 1, lo - 1, fill);
    lane_fill(row, hi + 1, m, fill);
  } else if (lo >= 2) {
    lane_fill(row, lo - 1, lo - 1, fill);
  }
}

#define ET_LANES for (int l = 0; l < kLanes; ++l)

void dtw_lanes(const Bank& A, const Bank& B, const int64_t* ia, const int64_t* jb, int64_t window, double* out,
               Scratch& s) {
  const int64_t n = A.len(ia[0]), m = B.len(jb[0]);
  const int64_t w = resolve_window(n, m, window, false);
  const double* xs[kLanes];
  const double* ys[kLanes];
  for (int l = 0; l < kLanes; ++l) {
    xs[l] = A.row(ia[l], 0);
    ys[l] = B.row(jb[l], 0);
  }
  pack(s.xa, xs, n);
  pack(s.xb, ys, m);
  s.lp.assign(static_cast<size_t>((m + 1) * kLanes), kInf);
  s.lc.assign(static_cast<size_t>((m + 1) * kLanes), kInf);
  double* __restrict p = s.lp.data();
  double* __restrict c = s.lc.data();
  const double* __restrict X = s.xa.data();
  const double* __restrict Y = s.xb.data();
  ET_LANES p[l] = 0.0;
  for (int64_t i = 1; i <= n; ++i) {
    int64_t lo, hi;
    window_bounds(i, m, w, lo, hi);
    ET_LANES c[l] = kInf;
    if (w >= 0) lane_reset_outside(c, i, lo, hi, m, kInf);
    const double* x = X + (i - 1) * kLanes;
    for (int64_t j = lo; j <= hi; ++j) {
      const double* y = Y + (j - 1) * kLanes;
      double* cj = c + j * kLanes;
      const double* cj1 = c + (j - 1) * kLanes;
      const double* pj = p + j * kLanes;
      const double* pj1 = p + (j - 1) * kLanes;
      for (int h = 0; h < kLanes; h += kVW) {
        const Lane cost = vabs(LD(y) - LD(x));
        Lane r = LD(pj);
        r = vmin_first(r, LD(cj1));
        r = vmin_first(r, LD(pj1));
        vstore(cj + h, cost + r);
      }
    }
    std::swap(p, c);
  }
  ET_LANES out[l] = p[m * kLanes + l];
}

void erp_lanes(const Bank& A, const RowScalars& GA, const Bank& B, const RowScalars& GB, const int64_t* ia,
               const int64_t* jb, int64_t window, bool fast, double* out, Scratch& s) {
  const int64_t n = A.len(ia[0]), m = B.len(jb[0]);
  const int64_t w = resolve_window(n, m, window, fast);
  const double* xs[kLanes];
  const double* ys[kLanes];
  const double* gx[kLanes];
  const double* gy[kLanes];
  for (int l = 0; l < kLanes; ++l) {
    xs[l] = A.row(ia[l], 0);
    ys[l] = B.row(jb[l], 0);
    gx[l] = GA.at(ia[l]);
    gy[l] = GB.at(jb[l]);
  }
  pack(s.xa, xs, n);
  pack(s.xb, ys, m);
  pack(s.da, gx, n);
  pack(s.db, gy, m);
  s.lp.assign(static_cast<size_t>((m + 1) * kLanes), kInf);
  s.lc.assign(static_cast<size_t>((m + 1) * kLanes), kInf);
  double* __restrict p = s.lp.data();
  double* __restrict c = s.lc.data();
  const double* __restrict X = s.xa.data();
  const double* __restrict Y = s.xb.data();
  const double* __restrict LG = s.da.data();
  const double* __restrict RG = s.db.data();
  ET_LANES p[l] = 0.0;
  for (int64_t j = 1; j <= m; ++j) ET_LANES p[j * kLanes + l] = p[(j - 1) * kLanes + l] + RG[(j - 1) * kLanes + l];
  for (int64_t i = 1; i <= n; ++i) {
    int64_t lo, hi;
    window_bounds(i, m, w, lo, hi);
    const double* lg = LG + (i - 1) * kLanes;
    ET_LANES c[l] = p[l] + lg[l];
    if (w >= 0) lane_reset_outside(c, i, lo, hi, m, kInf);
    const double* x = X + (i - 1) * kLanes;
    for (int64_t j = lo; j <= hi; ++j) {
      const double* y = Y + (j - 1) * kLanes;
      const double* rg = RG + (j - 1) * kLanes;
      double* cj = c + j * kLanes;
      const double* cj1 = c + (j - 1) * kLanes;
      const double* pj = p + j * kLanes;
      const double* pj1 = p + (j - 1) * kLanes;
      for (int h = 0; h < kLanes; h += kVW) {
        const Lane pair = vabs(LD(y) - LD(x));
        Lane r = LD(pj1) + pair;
        r = vmin_first(r, LD(pj) + LD(lg));
        r = vmin_first(r, LD(cj1) + LD(rg));
        vstore(cj + h, r);
      }
    }
    std::swap(p, c);
  }
  ET_LANES out[l] = p[m * kLanes + l];
}

void edr_lanes(const Bank& A, const Bank& B, const int64_t* ia, const int64_t* jb, double eps, bool normalized,
               int64_t window, bool fast, double* out, Scratch& s) {
  const int64_t n = A.len(ia[0]), m = B.len(jb[0]);
  const int64_t w = resolve_window(n, m, window, fast);
  const double* xs[kLanes];
  const double* ys[kLanes];
  for (int l = 0; l < kLanes; ++l) {
    xs[l] = A.row(ia[l], 0);
    ys[l] = B.row(jb[l], 0);
  }
  pack(s.xa, xs, n);
  pack(s.xb, ys, m);
  s.lp.assign(static_cast<size_t>((m + 1) * kLanes), kInf);
  s.lc.assign(static_cast<size_t>((m + 1) * kLanes), kInf);
  double* __restrict p = s.lp.data();
  double* __restrict c = s.lc.data();
  const double* __restrict X = s.xa.data();
  const double* __restrict Y = s.xb.data();
  for (int64_t j = 0; j <= m; ++j) ET_LANES p[j * kLanes + l] = static_cast<double>(j);
  for (int64_t i = 1; i <= n; ++i) {
    int64_t lo, hi;
    window_bounds(i, m, w, lo, hi);
    const double di = static_cast<double>(i);
    ET_LANES c[l] = di;
    if (w >= 0) lane_reset_outside(c, i, lo, hi, m, kInf);
    const double* x = X + (i - 1) * kLanes;
    for (int64_t j = lo; j <= hi; ++j) {
      const double* y = Y + (j - 1) * kLanes;
      double* cj = c + j * kLanes;
      const double* cj1 = c + (j - 1) * kLanes;
      const double* pj = p + j * kLanes;
      const double* pj1 = p + (j - 1) * kLanes;
      for (int h = 0; h < kLanes; h += kVW) {
        const Lane sub = vle_zero_one(vabs(LD(y) - LD(x)), eps);
        Lane r = LD(pj) + 1.0;
        r = vmin_first(r, LD(cj1) + 1.0);
        r = vmin_first(r, LD(pj1) + sub);
        vstore(cj + h, r);
      }
    }
    std::swap(p, c);
  }
  const double scale = static_cast<double>(std::max<int64_t>(1, std::max(n, m)));
  ET_LANES out[l] = normalized ? p[m * kLanes + l] / scale : p[m * kLanes + l];
}

void lcss_lanes(const Bank& A, const Bank& B, const int64_t* ia, const int64_t* jb, double eps, int64_t window,
                bool fast, double* out, Scratch& s) {
  const int64_t n = A.len(ia[0]), m = B.len(jb[0]);
  const int64_t w = resolve_window(n, m, window, fast);
  const double* xs[kLanes];
  const double* ys[kLanes];
  for (int l = 0; l < kLanes; ++l) {
    xs[l] = A.row(ia[l], 0);
    ys[l] = B.row(jb[l], 0);
  }
  pack(s.xa, xs, n);
  pack(s.xb, ys, m);
  s.lp.assign(static_cast<size_t>((m + 1) * kLanes), 0.0);
  s.lc.assign(static_cast<size_t>((m + 1) * kLanes), 0.0);
  double* __restrict p = s.lp.data();
  double* __restrict c = s.lc.data();
  const double* __restrict X = s.xa.data();
  const double* __restrict Y = s.xb.data();
  for (int64_t i = 1; i <= n; ++i) {
    int64_t lo, hi;
    window_bounds(i, m, w, lo, hi);
    ET_LANES c[l] = 0.0;
    if (w >= 0) lane_reset_outside(c, i, lo, hi, m, 0.0);
    const double* x = X + (i - 1) * kLanes;
    for (int64_t j = lo; j <= hi; ++j) {
      const double* y = Y + (j - 1) * kLanes;
      double* cj = c + j * kLanes;
      const double* cj1 = c + (j - 1) * kLanes;
      const double* pj = p + j * kLanes;
      const double* pj1 = p + (j - 1) * kLanes;
      for (int h = 0; h < kLanes; h += kVW) {
        vstore(cj + h, vlcss(LD(pj1), LD(cj1), LD(pj), vabs(LD(y) - LD(x)), eps));
      }
    }
    std::swap(p, c);
  }
  const double scale = static_cast<double>(std::max<int64_t>(1, std::min(n, m)));
  ET_LANES out[l] = p[m * kLanes + l] / scale;
}

void twed_lanes(const TwedSide& L, const TwedSide& R, const int64_t* ia, const int64_t* jb, double nu,
                int64_t window, bool fast, double* out, Scratch& s) {
  const int64_t n = L.values.len(ia[0]), m = R.values.len(jb[0]);
  const int64_t w = resolve_window(n, m, window, fast);
  const double* src[kLanes];
  for (int l = 0; l < kLanes; ++l) src[l] = L.values.row(ia[l], 0);
  pack(s.xa, src, n);
  for (int l = 0; l < kLanes; ++l) src[l] = L.prev_values.row(ia[l], 0);
  pack(s.xpa, src, n);
  for (int l = 0; l < kLanes; ++l) src[l] = L.t.at(ia[l]);
  pack(s.ta, src, n);
  for (int l = 0; l < kLanes; ++l) src[l] = L.tprev.at(ia[l]);
  pack(s.tpa, src, n);
  for (int l = 0; l < kLanes; ++l) src[l] = L.del.at(ia[l]);
  pack(s.da, src, n);
  for (int l = 0; l < kLanes; ++l) src[l] = R.values.row(jb[l], 0);
  pack(s.xb, src, m);
  for (int l = 0; l < kLanes; ++l) src[l] = R.prev_values.row(jb[l], 0);
  pack(s.xpb, src, m);
  for (int l = 0; l < kLanes; ++l) src[l] = R.t.at(jb[l]);
  pack(s.tb, src, m);
  for (int l = 0; l < kLanes; ++l) src[l] = R.tprev.at(jb[l]);
  pack(s.tpb, src, m);
  for (int l = 0; l < kLanes; ++l) src[l] = R.del.at(jb[l]);
  pack(s.db, src, m);
  s.lp.assign(static_cast<size_t>((m + 1) * kLanes), kInf);
  s.lc.assign(static_cast<size_t>((m + 1) * kLanes), kInf);
  double* __restrict p = s.lp.data();
  double* __restrict c = s.lc.data();
  const double* __restrict X = s.xa.data();
  const double* __restrict XP = s.xpa.data();
  const double* __restrict TX = s.ta.data();
  const double* __restrict TXP = s.tpa.data();
  const double* __restrict LD = s.da.data();
  const double* __restrict Y = s.xb.data();
  const double* __restrict YP = s.xpb.data();
  const double* __restrict TY = s.tb.data();
  const double* __restrict TYP = s.tpb.data();
  const double* __restrict RD = s.db.data();
  ET_LANES p[l] = 0.0;
  for (int64_t i = 1; i <= n; ++i) {
    int64_t lo, hi;
    window_bounds(i, m, w, lo, hi);
    ET_LANES c[l] = kInf;
    if (w >= 0) lane_reset_outside(c, i, lo, hi, m, kInf);
    const double* x = X + (i - 1) * kLanes;
    const double* xp = XP + (i - 1) * kLanes;
    const double* tx = TX + (i - 1) * kLanes;
    const double* txp = TXP + (i - 1) * kLanes;
    const double* ld = LD + (i - 1) * kLanes;
    for (int64_t j = lo; j <= hi; ++j) {
      const double* y = Y + (j - 1) * kLanes;
      const double* yp = YP + (j - 1) * kLanes;
      const double* ty = TY + (j - 1) * kLanes;
      const double* typ = TYP + (j - 1) * kLanes;
      const double* rd = RD + (j - 1) * kLanes;
      double* cj = c + j * kLanes;
      const double* cj1 = c + (j - 1) * kLanes;
      const double* pj = p + j * kLanes;
      const double* pj1 = p + (j - 1) * kLanes;
      for (int h = 0; h < kLanes; h += kVW) {
        const Lane pair = vabs(LD(y) - LD(x));
        const Lane pair_prev = vabs(LD(yp) - LD(xp));
        const Lane time_cost = nu * (vabs(LD(tx) - LD(ty)) + vabs(LD(txp) - LD(typ)));
        Lane r = LD(pj) + LD(ld);
        r = vmin_first(r, LD(cj1) + LD(rd));
        r = vmin_first(r, LD(pj1) + pair + pair_prev + time_cost);
        vstore(cj + h, r);
      }
    }
    std::swap(p, c);
  }
  ET_LANES out[l] = p[m * kLanes + l];
}

#undef ET_LANES
#undef LD

// ---------------------------------------------------------- dispatcher ----
// Pairs are ordered by (len_a, len_b). With lanes enabled (univariate input),
// each full group of kLanes pairs with equal lengths goes to the lane kernel;
// the rest run the scalar kernel. Work items are scheduled dynamically.
template <class LaneFn, class OneFn>
py::array_t<double> run_pairs(const Bank& A, const Bank& B, const arr_i& I, const arr_i& J, int n_threads,
                              bool lanes_ok, LaneFn&& lane, OneFn&& one) {
  const int64_t K = I.shape(0);
  py::array_t<double> out(K);
  double* po = out.mutable_data();
  const int64_t* pi = I.data();
  const int64_t* pj = J.data();
  {
    py::gil_scoped_release release;
    std::vector<int64_t> order(static_cast<size_t>(K));
    for (int64_t k = 0; k < K; ++k) order[k] = k;
    struct Item {
      int64_t start;
      int count;
    };
    std::vector<Item> items;
    if (lanes_ok) {
      std::stable_sort(order.begin(), order.end(), [&](int64_t u, int64_t v) {
        const int64_t nu = A.len(pi[u]), nv = A.len(pi[v]);
        if (nu != nv) return nu < nv;
        return B.len(pj[u]) < B.len(pj[v]);
      });
      int64_t k = 0;
      while (k < K) {
        int64_t e = k;
        const int64_t n0 = A.len(pi[order[k]]), m0 = B.len(pj[order[k]]);
        while (e < K && A.len(pi[order[e]]) == n0 && B.len(pj[order[e]]) == m0) ++e;
        const bool usable = n0 > 0 && m0 > 0;
        for (; usable && k + kLanes <= e; k += kLanes) items.push_back({k, kLanes});
        for (; k < e; ++k) items.push_back({k, 1});
      }
    } else {
      items.reserve(static_cast<size_t>(K));
      for (int64_t k = 0; k < K; ++k) items.push_back({k, 1});
    }
    const int t = resolve_threads(n_threads, static_cast<int64_t>(items.size()));
    std::vector<Scratch> scratch(static_cast<size_t>(std::max(t, 1)));
    parallel_for(static_cast<int64_t>(items.size()), t, [&](int64_t it, int tid) {
      const Item item = items[static_cast<size_t>(it)];
      Scratch& s = scratch[static_cast<size_t>(tid)];
      if (item.count == kLanes) {
        int64_t ia[kLanes], jb[kLanes];
        double res[kLanes];
        for (int l = 0; l < kLanes; ++l) {
          ia[l] = pi[order[item.start + l]];
          jb[l] = pj[order[item.start + l]];
        }
        lane(ia, jb, res, s);
        for (int l = 0; l < kLanes; ++l) po[order[item.start + l]] = res[l];
      } else {
        const int64_t k = order[item.start];
        po[k] = one(pi[k], pj[k], s.prev, s.curr, s.buf);
      }
    });
  }
  return out;
}

py::array_t<double> lcss_pairs(const arr_d& va, const arr_i& oa, const arr_d& vb, const arr_i& ob, const arr_i& I,
                               const arr_i& J, double eps, int64_t window, bool fast, int n_threads) {
  const Bank A = make_bank(va, oa), B = make_bank(vb, ob);
  check_pairs(I, J, A, B);
  return run_pairs(
      A, B, I, J, n_threads, A.d == 1,
      [&](const int64_t* ia, const int64_t* jb, double* res, Scratch& s) { lcss_lanes(A, B, ia, jb, eps, window, fast, res, s); },
      [&](int64_t a, int64_t b, auto& p, auto& c, auto& buf) {
        return A.d == 1 ? lcss_one<true>(A, a, B, b, eps, window, fast, p, c, buf)
                        : lcss_one<false>(A, a, B, b, eps, window, fast, p, c, buf);
      });
}

py::array_t<double> edr_pairs(const arr_d& va, const arr_i& oa, const arr_d& vb, const arr_i& ob, const arr_i& I,
                              const arr_i& J, double eps, bool normalized, int64_t window, bool fast, int n_threads) {
  const Bank A = make_bank(va, oa), B = make_bank(vb, ob);
  check_pairs(I, J, A, B);
  return run_pairs(
      A, B, I, J, n_threads, A.d == 1,
      [&](const int64_t* ia, const int64_t* jb, double* res, Scratch& s) { edr_lanes(A, B, ia, jb, eps, normalized, window, fast, res, s); },
      [&](int64_t a, int64_t b, auto& p, auto& c, auto& buf) {
        return A.d == 1 ? edr_one<true>(A, a, B, b, eps, normalized, window, fast, p, c, buf)
                        : edr_one<false>(A, a, B, b, eps, normalized, window, fast, p, c, buf);
      });
}

py::array_t<double> erp_pairs(const arr_d& va, const arr_i& oa, const arr_d& ga, const arr_d& vb, const arr_i& ob,
                              const arr_d& gb, const arr_i& I, const arr_i& J, int64_t window, bool fast,
                              int n_threads) {
  const Bank A = make_bank(va, oa), B = make_bank(vb, ob);
  check_pairs(I, J, A, B);
  const RowScalars GA = make_rows(ga, A, "gap costs A"), GB = make_rows(gb, B, "gap costs B");
  return run_pairs(
      A, B, I, J, n_threads, A.d == 1,
      [&](const int64_t* ia, const int64_t* jb, double* res, Scratch& s) { erp_lanes(A, GA, B, GB, ia, jb, window, fast, res, s); },
      [&](int64_t a, int64_t b, auto& p, auto& c, auto& buf) {
        return A.d == 1 ? erp_one<true>(A, a, GA, B, b, GB, window, fast, p, c, buf)
                        : erp_one<false>(A, a, GA, B, b, GB, window, fast, p, c, buf);
      });
}

TwedSide make_twed_side(const arr_d& v, const arr_d& pv, const arr_i& o, const arr_d& t, const arr_d& tp,
                        const arr_d& del) {
  TwedSide s;
  s.values = make_bank(v, o);
  s.prev_values = make_bank(pv, o);
  if (s.prev_values.d != s.values.d) throw std::invalid_argument("previous rows must match values");
  s.t = make_rows(t, s.values, "timestamps");
  s.tprev = make_rows(tp, s.values, "previous timestamps");
  s.del = make_rows(del, s.values, "delete costs");
  return s;
}

py::array_t<double> twed_pairs(const arr_d& va, const arr_d& pva, const arr_i& oa, const arr_d& ta, const arr_d& tpa,
                               const arr_d& dela, const arr_d& vb, const arr_d& pvb, const arr_i& ob,
                               const arr_d& tb, const arr_d& tpb, const arr_d& delb, const arr_i& I, const arr_i& J,
                               double nu, int64_t window, bool fast, int n_threads) {
  const TwedSide L = make_twed_side(va, pva, oa, ta, tpa, dela);
  const TwedSide R = make_twed_side(vb, pvb, ob, tb, tpb, delb);
  check_pairs(I, J, L.values, R.values);
  return run_pairs(
      L.values, R.values, I, J, n_threads, L.values.d == 1,
      [&](const int64_t* ia, const int64_t* jb, double* res, Scratch& s) { twed_lanes(L, R, ia, jb, nu, window, fast, res, s); },
      [&](int64_t a, int64_t b, auto& p, auto& c, auto& buf) {
        return L.values.d == 1 ? twed_one<true>(L, a, R, b, nu, window, fast, p, c, buf)
                               : twed_one<false>(L, a, R, b, nu, window, fast, p, c, buf);
      });
}

py::array_t<double> dtw_pairs(const arr_d& va, const arr_i& oa, const arr_d& vb, const arr_i& ob, const arr_i& I,
                              const arr_i& J, int64_t window, int n_threads) {
  const Bank A = make_bank(va, oa), B = make_bank(vb, ob);
  check_pairs(I, J, A, B);
  return run_pairs(
      A, B, I, J, n_threads, A.d == 1,
      [&](const int64_t* ia, const int64_t* jb, double* res, Scratch& s) { dtw_lanes(A, B, ia, jb, window, res, s); },
      [&](int64_t a, int64_t b, auto& p, auto& c, auto& buf) {
        return A.d == 1 ? dtw_one<true>(A, a, B, b, window, p, c, buf)
                        : dtw_one<false>(A, a, B, b, window, p, c, buf);
      });
}

// ------------------------------------------------------ sample entropy ----
// metrics.sample_entropy._phi counts: for i in [0, n-order), j in (i, n-order],
// count += max|x[i+k] - x[j+k]| <= r. NaN differences never match, as with
// np.max(...) <= r. Returns (count, templates) as exact integers.
std::pair<int64_t, int64_t> sampen_phi_counts(const double* x, int64_t n, int64_t order, double r) {
  int64_t count = 0, templates = 0;
  for (int64_t i = 0; i < n - order; ++i) {
    for (int64_t j = i + 1; j < n - order + 1; ++j) {
      bool ok = true;
      for (int64_t k = 0; k < order; ++k) {
        const double diff = std::fabs(x[i + k] - x[j + k]);
        if (!(diff <= r)) {
          ok = false;
          break;
        }
      }
      if (ok) ++count;
    }
    templates += n - order - i;
  }
  return {count, templates};
}

py::tuple sample_entropy_counts(const arr_d& x, int64_t order, double r) {
  if (x.ndim() != 1) throw std::invalid_argument("x must be 1-D");
  const double* px = x.data();
  const int64_t n = x.shape(0);
  std::pair<int64_t, int64_t> res;
  {
    py::gil_scoped_release release;
    res = sampen_phi_counts(px, n, order, r);
  }
  return py::make_tuple(res.first, res.second);
}

// Batched over a bank of univariate series: returns (S, 4) int64 with
// (count_m, templates_m, count_m1, templates_m1) per series and per-series r.
py::array_t<int64_t> sample_entropy_counts_bank(const arr_d& v, const arr_i& o, const arr_d& r, int64_t order,
                                                int n_threads) {
  const Bank B = make_bank(v, o);
  if (B.d != 1) throw std::invalid_argument("sample entropy bank must be univariate");
  if (r.ndim() != 1 || r.shape(0) != B.S) throw std::invalid_argument("r must have one value per series");
  py::array_t<int64_t> out({B.S, static_cast<int64_t>(4)});
  int64_t* po = out.mutable_data();
  const double* pr = r.data();
  {
    py::gil_scoped_release release;
    parallel_for(B.S, n_threads, [&](int64_t s, int) {
      const double* x = B.row(s, 0);
      const int64_t n = B.len(s);
      const auto a = sampen_phi_counts(x, n, order, pr[s]);
      const auto b = sampen_phi_counts(x, n, order + 1, pr[s]);
      po[s * 4 + 0] = a.first;
      po[s * 4 + 1] = a.second;
      po[s * 4 + 2] = b.first;
      po[s * 4 + 3] = b.second;
    });
  }
  return out;
}

}  // namespace

PYBIND11_MODULE(_echotime_native, m) {
  m.doc() = "EchoTime native kernels (bit-identical to the pure-Python reference).";
  m.attr("ABI_VERSION") = 1;
  m.def("hardware_concurrency", []() { return static_cast<int>(std::thread::hardware_concurrency()); });
  m.def("lcss_pairs", &lcss_pairs, py::arg("values_a"), py::arg("offsets_a"), py::arg("values_b"),
        py::arg("offsets_b"), py::arg("I"), py::arg("J"), py::arg("epsilon"), py::arg("window"), py::arg("fast"),
        py::arg("n_threads"));
  m.def("edr_pairs", &edr_pairs, py::arg("values_a"), py::arg("offsets_a"), py::arg("values_b"),
        py::arg("offsets_b"), py::arg("I"), py::arg("J"), py::arg("epsilon"), py::arg("normalized"),
        py::arg("window"), py::arg("fast"), py::arg("n_threads"));
  m.def("erp_pairs", &erp_pairs, py::arg("values_a"), py::arg("offsets_a"), py::arg("gap_costs_a"),
        py::arg("values_b"), py::arg("offsets_b"), py::arg("gap_costs_b"), py::arg("I"), py::arg("J"),
        py::arg("window"), py::arg("fast"), py::arg("n_threads"));
  m.def("twed_pairs", &twed_pairs, py::arg("values_a"), py::arg("prev_values_a"), py::arg("offsets_a"),
        py::arg("t_a"), py::arg("t_prev_a"), py::arg("delete_a"), py::arg("values_b"), py::arg("prev_values_b"),
        py::arg("offsets_b"), py::arg("t_b"), py::arg("t_prev_b"), py::arg("delete_b"), py::arg("I"), py::arg("J"),
        py::arg("nu"), py::arg("window"), py::arg("fast"), py::arg("n_threads"));
  m.def("dtw_pairs", &dtw_pairs, py::arg("values_a"), py::arg("offsets_a"), py::arg("values_b"),
        py::arg("offsets_b"), py::arg("I"), py::arg("J"), py::arg("window"), py::arg("n_threads"));
  m.def("sample_entropy_counts", &sample_entropy_counts, py::arg("x"), py::arg("order"), py::arg("r"));
  m.def("sample_entropy_counts_bank", &sample_entropy_counts_bank, py::arg("values"), py::arg("offsets"),
        py::arg("r"), py::arg("order"), py::arg("n_threads"));
}
