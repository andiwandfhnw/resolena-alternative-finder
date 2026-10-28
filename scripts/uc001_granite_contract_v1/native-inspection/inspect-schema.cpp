#include "json-schema-to-grammar.h"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>

int main(int argc, char ** argv) {
    try {
        if (argc != 3) {
            throw std::runtime_error("Usage: granite-inspect-schema frozen-schema.json new-output.gbnf");
        }
        const std::filesystem::path input(argv[1]);
        const std::filesystem::path output(argv[2]);
        if (!std::filesystem::is_regular_file(input) || std::filesystem::file_size(input) > 1048576) {
            throw std::runtime_error("Schema must be a regular file of at most 1 MiB");
        }
        if (std::filesystem::exists(output)) {
            throw std::runtime_error("Refusing to overwrite an existing output");
        }
        std::ifstream source(input, std::ios::binary);
        if (!source) {
            throw std::runtime_error("Cannot open schema");
        }
        const std::string text((std::istreambuf_iterator<char>(source)), std::istreambuf_iterator<char>());
        const auto schema = common_json::parse(text);
        if (!schema.is_object()) {
            throw std::runtime_error("Schema must be an object");
        }
        const auto grammar = json_schema_to_grammar(schema, true);
        if (grammar.empty() || grammar.find("root ::=") == std::string::npos) {
            throw std::runtime_error("Native conversion returned no root grammar");
        }
        std::ofstream destination(output, std::ios::binary | std::ios::out);
        destination.write(grammar.data(), static_cast<std::streamsize>(grammar.size()));
        destination.flush();
        if (!destination) {
            throw std::runtime_error("Cannot write grammar");
        }
        return 0;
    } catch (const std::exception & error) {
        std::cerr << "Schema inspection failed: " << error.what() << '\n';
        return 1;
    }
}
