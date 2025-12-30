#ifndef FILE_UTILS_HPP
#define FILE_UTILS_HPP

#include <string>
#include <vector>

namespace FileUtils
{
    bool fileExists(const std::string &path);
    bool directoryExists(const std::string &path);
    std::string readFile(const std::string &path);
    bool writeFile(const std::string &path, const std::string &content);
    std::vector<std::string> listFiles(const std::string &directory, const std::string &extension = "");
    std::string getAbsolutePath(const std::string &path);
    std::string getFileName(const std::string &path);
    std::string getFileExtension(const std::string &path);
}

#endif // FILE_UTILS_HPP
