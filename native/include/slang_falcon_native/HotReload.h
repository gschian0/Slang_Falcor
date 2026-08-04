#pragma once

#include <filesystem>
#include <functional>
#include <string>
#include <unordered_map>
#include <vector>

namespace slang_falcon {

/// Simple mtime watcher for hot-reloading Slang modules (F5 or poll).
class HotReload {
public:
    using Callback = std::function<void(const std::filesystem::path&)>;

    void watch(const std::filesystem::path& path, Callback onChange);
    /// Poll watched files; invoke callbacks when mtime changes. Returns #reloads.
    int poll();
    /// Force-fire all callbacks (e.g. user pressed F5).
    void forceReload();

private:
    struct Entry {
        std::filesystem::path path;
        std::filesystem::file_time_type mtime{};
        Callback callback;
    };
    std::vector<Entry> entries_;
};

}  // namespace slang_falcon
