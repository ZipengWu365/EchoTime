from echotime import mcp_tool_descriptors, ts_compare, ts_profile, ts_route

TOOLS = mcp_tool_descriptors(format='dict')['tools']
REGISTRY = {'ts_profile': ts_profile, 'ts_compare': ts_compare, 'ts_route': ts_route}

# Plug TOOLS and REGISTRY into the MCP framework of your choice.
print(TOOLS)
