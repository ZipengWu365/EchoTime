module.exports = {
  theme: {
    extend: {
      colors: {
        page: "#FFFFFF",
        card: "#FAFAFA",
        border: "#E5E7EB",
        text: {
          DEFAULT: "#1F2937",
          muted: "#6B7280",
        },
        sun: {
          100: "#FFF4C2",
          300: "#FFE27A",
          500: "#FFC83D",
          700: "#C7950A",
        },
        science: {
          600: "#2F6BFF",
          700: "#2554CC",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Helvetica", "Arial", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Consolas", "Menlo", "monospace"],
      },
      borderRadius: {
        sm: "14px",
        md: "20px",
        lg: "28px",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(31, 41, 55, 0.06)",
        lift: "0 18px 50px rgba(31, 41, 55, 0.08)",
      },
    },
  },
};
