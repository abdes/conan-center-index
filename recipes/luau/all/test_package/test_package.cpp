#include <Luau/Compiler.h>
#include <lua.h>
#include <lualib.h>

#include <memory>
#include <string>

namespace {
int Traceback(lua_State* state) {
    luaL_traceback(state, state, lua_tostring(state, 1), 1);
    return 1;
}
}

int main() {
    const auto state = std::unique_ptr<lua_State, decltype(&lua_close)>(
        luaL_newstate(), &lua_close);
    if (!state) return 1;
    auto* const lua = state.get();
    luaL_openlibs(lua);
    const auto failing = Luau::compile("error('expected failure')");
    const auto healthy = Luau::compile("return 42");
    // Exercise protected error recovery repeatedly, followed by healthy code.
    // This exposed corrupted VM call-depth state in the previous MSVC package.
    for (int iteration = 0; iteration < 16; ++iteration) {
        lua_pushcfunction(lua, Traceback, "traceback");
        if (luau_load(lua, "failing", failing.data(), failing.size(), 0) != 0) return 2;
        if (lua_pcall(lua, 0, 0, 1) != LUA_ERRRUN) return 3;
        const auto* error = lua_tostring(lua, -1);
        if (!error || std::string(error).find("expected failure") == std::string::npos) return 4;
        lua_settop(lua, 0);
        if (luau_load(lua, "healthy", healthy.data(), healthy.size(), 0) != 0) return 5;
        if (lua_pcall(lua, 0, 1, 0) != LUA_OK || lua_tonumber(lua, -1) != 42) return 6;
        lua_settop(lua, 0);
    }
    return 0;
}
