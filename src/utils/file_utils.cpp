#include "utils/file_utils.hpp"
#include <filesystem>
#include <fstream>

namespace fs = std::filesystem;

namespace FileUtils
{

    bool fileExists(const std::string &path)
    {
        return fs::exists(path) && fs::is_regular_file(path);
    }

    bool directoryExists(const std::string &path)
    {
        return fs::exists(path) && fs::is_directory(path);
    }

    std::string readFile(const std::string &path)
    {
        if (!fileExists(path))
        {
            return "";
        }

        std::ifstream file(path);
        return std::string((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    }

    bool writeFile(const std::string &path, const std::string &content)
    {
        try
        {
            std::ofstream file(path);
            file << content;
            return true;
        }
        catch (const std::exception &e)
        {
            return false;
        }
    }

    std::vector<std::string> listFiles(const std::string &directory, const std::string &extension)
    {
        std::vector<std::string> files;

        if (!directoryExists(directory))
        {
            return files;
        }

        try
        {
            for (const auto &entry : fs::directory_iterator(directory))
            {
                if (entry.is_regular_file())
                {
                    if (extension.empty() || entry.path().extension().string() == extension)
                    {
                        files.push_back(entry.path().filename().string());
                    }
                }
            }
        }
        catch (const std::exception &e)
        {
            // TODO: Log l'erreur
        }

        return files;
    }

    std::string getAbsolutePath(const std::string &path)
    {
        return fs::absolute(path).string();
    }

    std::string getFileName(const std::string &path)
    {
        return fs::path(path).filename().string();
    }

    std::string getFileExtension(const std::string &path)
    {
        return fs::path(path).extension().string();
    }

} // namespace FileUtils
