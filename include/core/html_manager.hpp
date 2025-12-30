#ifndef HTML_MANAGER_HPP
#define HTML_MANAGER_HPP

#include <string>
#include <vector>

struct EditableElement
{
    int index;
    std::string tag;
    std::string id;
    std::string content;
    bool is_iframe;
    std::string editable_value;
};

struct HTMLResult
{
    bool success;
    std::string error;
    std::vector<EditableElement> elements;
    int count;
};

class HTMLManager
{
public:
    HTMLManager();
    ~HTMLManager();

    HTMLResult extractEditableElements(const std::string &file_path);
    bool saveFile(const std::string &file_path, const std::vector<EditableElement> &elements);
    std::string readFile(const std::string &file_path);
    bool writeFile(const std::string &file_path, const std::string &content);

private:
    EditableElement parseElement(void *element_node, int index);
};

#endif // HTML_MANAGER_HPP
