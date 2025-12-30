#ifndef LOGGER_HPP
#define LOGGER_HPP

#include <string>
#include <vector>
#include <fstream>
#include <mutex>

class Logger
{
public:
    Logger();
    ~Logger();

    void log(const std::string &message);
    void error(const std::string &message);
    void warning(const std::string &message);
    void info(const std::string &message);

    std::vector<std::string> getLogs() const;
    void clearLogs();
    void exportLogs(const std::string &file_path) const;

private:
    void writeToFile(const std::string &level, const std::string &message);
    std::string getTimestamp() const;

    std::vector<std::string> m_logs;
    std::string m_logFilePath;
    std::ofstream m_logFile;
    mutable std::mutex m_mutex;
};

#endif // LOGGER_HPP
