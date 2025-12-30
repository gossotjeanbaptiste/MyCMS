#ifndef PYTHON_BUILDER_HPP
#define PYTHON_BUILDER_HPP

#include <string>

struct BuildResult
{
    bool success;
    std::string output;
    std::string error;
};

class PythonBuilder
{
public:
    PythonBuilder();
    ~PythonBuilder() = default;

    BuildResult buildExecutable(const std::string &script_path, const std::string &output_path);
    std::string getLastOutput() const;

private:
    std::string m_lastOutput;
};

#endif // PYTHON_BUILDER_HPP
