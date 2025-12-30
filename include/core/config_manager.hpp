#ifndef CONFIG_MANAGER_HPP
#define CONFIG_MANAGER_HPP

#include <string>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

class ConfigManager
{
public:
    ConfigManager();
    ~ConfigManager() = default;

    void loadConfig(const std::string &file_path = "");
    void saveConfig();

    std::string getRepoPath() const;
    void setRepoPath(const std::string &path);

    bool getAutoPull() const;
    void setAutoPull(bool value);

    bool getAutoRefresh() const;
    void setAutoRefresh(bool value);

    int getDefaultPort() const;
    void setDefaultPort(int port);

private:
    std::string getConfigPath() const;
    void createDefaultConfig();

    json m_config;
    std::string m_configFilePath;
};

#endif // CONFIG_MANAGER_HPP
