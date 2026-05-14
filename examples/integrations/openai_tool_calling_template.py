from echotime import openai_function_schemas, ts_profile

functions = openai_function_schemas(format='dict')['functions']
# Register `functions` with your tool-calling client and map `ts_profile` to the real Python function.

example = ts_profile([0.0, 1.0, 0.5, 1.2], budget='lean')
print(example)
