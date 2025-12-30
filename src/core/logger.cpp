#include "core/logger.hpp"
#include <iostream>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <filesystem>

namespace fs = std::filesystem;

Logger::Logger()
{
    // TODO: Créer le fichier log dans le répertoire utilisateur
    std::string log_dir = "logs";
    if (!fs::exists(log_dir))
    {
        fs::create_directory(log_dir);
    }
    m_logFilePath = log_dir + "/mycms.log";
    m_logFile.open(m_logFilePath, std::ios::app);
}

Logger::~Logger()
{
    if (m_logFile.is_open())
    {
        m_logFile.close();
    }
}

void Logger::log(const std::string &message)
{
    info(message);
}

void Logger::error(const std::string &message)
{
    writeToFile("ERROR", message);
}

void Logger::warning(const std::string &message)
{
    writeToFile("WARNING", message);
}

void Logger::info(const std::string &message)
{
    writeToFile("INFO", message);
}

std::vector<std::string> Logger::getLogs() const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    return m_logs;
}

void Logger::clearLogs()
{
    std::lock_guard<std::mutex> lock(m_mutex);
    m_logs.clear();
}

void Logger::exportLogs(const std::string &file_path) const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    std::ofstream file(file_path);
    for (const auto &log : m_logs)
    {
        file << log << "\n";
    }
}

void Logger::writeToFile(const std::string &level, const std::string &message)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    std::string formatted = "[" + getTimestamp() + "] " + level + ": " + message;
    m_logs.push_back(formatted);
    if (m_logFile.is_open())
    {
        m_logFile << formatted << std::endl;
        m_logFile.flush();
    }
}

std::string Logger::getTimestamp() const
{
    auto now = std::time(nullptr);
    auto tm = *std::localtime(&now);
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
    return oss.str();
}
