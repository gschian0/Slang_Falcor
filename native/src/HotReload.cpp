#include "slang_falcon_native/HotReload.h"

#include <iostream>

namespace slang_falcon {

void HotReload::watch(const std::filesystem::path& path, Callback onChange) {
    Entry e;
    e.path = path;
    e.callback = std::move(onChange);
    std::error_code ec;
    if (std::filesystem::exists(path, ec))
        e.mtime = std::filesystem::last_write_time(path, ec);
    entries_.push_back(std::move(e));
}

int HotReload::poll() {
    int n = 0;
    for (auto& e : entries_) {
        std::error_code ec;
        if (!std::filesystem::exists(e.path, ec)) continue;
        auto mt = std::filesystem::last_write_time(e.path, ec);
        if (ec) continue;
        if (mt != e.mtime) {
            e.mtime = mt;
            if (e.callback) e.callback(e.path);
            ++n;
            std::cout << "[hot-reload] " << e.path << "\n";
        }
    }
    return n;
}

void HotReload::forceReload() {
    for (auto& e : entries_) {
        std::error_code ec;
        if (std::filesystem::exists(e.path, ec))
            e.mtime = std::filesystem::last_write_time(e.path, ec);
        if (e.callback) e.callback(e.path);
        std::cout << "[hot-reload:force] " << e.path << "\n";
    }
}

}  // namespace slang_falcon
