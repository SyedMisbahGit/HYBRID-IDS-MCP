# Simple Makefile for S-IDS (when CMake is not available)

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2 -I./src
LDFLAGS = -lpcap -lpthread

# Source files
SOURCES = src/nids/common/types.cpp \
          src/nids/parser/packet_parser.cpp \
          src/nids/rules/rule_engine.cpp \
          src/nids/sids_main.cpp

# Object files
OBJECTS = $(SOURCES:.cpp=.o)

# Target
TARGET = sids

# Default target
all: $(TARGET)

# Link
$(TARGET): $(OBJECTS)
	@echo "Linking $(TARGET)..."
	$(CXX) $(OBJECTS) $(LDFLAGS) -o $(TARGET)
	@echo "Build complete! Executable: ./$(TARGET)"

# Compile
%.o: %.cpp
	@echo "Compiling $<..."
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean
clean:
	@echo "Cleaning..."
	rm -f $(OBJECTS) $(TARGET)
	@echo "Clean complete!"

# Run tests
test: $(TARGET)
	@echo "Generating test traffic..."
	python3 scripts/generate_test_traffic.py test_traffic.pcap
	@echo "Running S-IDS..."
	./$(TARGET) -r test_traffic.pcap

.PHONY: all clean test
