#ifndef STRING_UTILS_HPP
#define STRING_UTILS_HPP

#include <string>
#include <vector>

namespace StringUtils
{
    std::string trim(const std::string &str);
    std::string toLower(const std::string &str);
    std::string toUpper(const std::string &str);
    std::vector<std::string> split(const std::string &str, char delimiter);
    bool startsWith(const std::string &str, const std::string &prefix);
    bool endsWith(const std::string &str, const std::string &suffix);
    std::string replace(const std::string &str, const std::string &from, const std::string &to);
    bool contains(const std::string &str, const std::string &substring);
}

#endif // STRING_UTILS_HPP
