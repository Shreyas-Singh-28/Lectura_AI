#include <iostream>
#include <fstream>
#include <cstdio>
#include <string>

using namespace std;

string executePythonScript(const string& filePath) {
    string command = "python transcribe.py \"" + filePath + "\"";
    char buffer[128];
    string result;
    
    FILE* pipe = _popen(command.c_str(), "r");
    if (!pipe) throw runtime_error("Failed to run Python script");

    while (fgets(buffer, sizeof(buffer), pipe)) {
        result += buffer;
    }

    int status = _pclose(pipe);
    if (status != 0) {
        throw runtime_error("Python script failed");
    }

    return result;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        cerr << "Usage: " << argv[0] << " <filepath>" << endl;
        return 1;
    }

    string filepath = argv[1];
    ifstream testFile(filepath);
    if (!testFile.good()) {
        cerr << "Error: File not accessible" << endl;
        return 1;
    }

    try {
        string output = executePythonScript(filepath);
        cout << output;
        return 0;
    } catch (const exception& e) {
        cerr << "Error: " << e.what() << endl;
        return 1;
    }
}