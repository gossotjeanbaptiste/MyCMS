#include "core/python_builder.hpp"

PythonBuilder::PythonBuilder()
{
    // TODO: Initialiser PyInstaller si nécessaire
}

BuildResult PythonBuilder::buildExecutable(const std::string &script_path, const std::string &output_path)
{
    BuildResult result;
    // TODO: Utiliser QProcess pour appeler pyinstaller
    result.success = false;
    result.error = "TODO: Implement buildExecutable";
    return result;
}

std::string PythonBuilder::getLastOutput() const
{
    return m_lastOutput;
}
