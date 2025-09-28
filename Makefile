# Makefile for House Judiciary Committee Hearing Analysis

# Default Python interpreter
PYTHON = python3

# Default target
.DEFAULT_GOAL := help

# Install dependencies
install:
	$(PYTHON) -m pip install -r requirements.txt

# Full judiciary analysis (scrape + attendance record)
judiciary:
	@if [ -z "$(LAST_NAME)" ]; then \
		echo "Usage: make judiciary LAST_NAME=<legislator_last_name>"; \
		echo "Example: make judiciary LAST_NAME=Jordan"; \
		exit 1; \
	fi
	@echo "Running full judiciary analysis for $(LAST_NAME)..."
	$(PYTHON) scrape_judiciary.py
	$(PYTHON) attendance_record.py $(LAST_NAME)

# Run comprehensive scraping (ALL hearings)
scrape:
	@echo "Running comprehensive judiciary hearing scraper (ALL hearings)..."
	$(PYTHON) scrape_judiciary.py

# Run legacy scraping (5 hearings only)
scrape-legacy:
	@echo "Running legacy judiciary hearing scraper (5 hearings only)..."
	$(PYTHON) scrape_judiciary.py --legacy

# Run comprehensive scraping with custom batch size
scrape-batch:
	@if [ -z "$(BATCH_SIZE)" ]; then \
		echo "Usage: make scrape-batch BATCH_SIZE=<number>"; \
		echo "Example: make scrape-batch BATCH_SIZE=20"; \
		exit 1; \
	fi
	@echo "Running comprehensive scraper with batch size $(BATCH_SIZE)..."
	$(PYTHON) scrape_judiciary.py --batch-size $(BATCH_SIZE)

# Run only attendance record generation
attendance:
	@if [ -z "$(LAST_NAME)" ]; then \
		echo "Usage: make attendance LAST_NAME=<legislator_last_name>"; \
		echo "Example: make attendance LAST_NAME=Jordan"; \
		exit 1; \
	fi
	@echo "Generating attendance record for $(LAST_NAME)..."
	$(PYTHON) attendance_record.py $(LAST_NAME)

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -f scrape_judiciary.json
	rm -f *_judiciary_*.xlsx
	rm -rf __pycache__
	rm -f *.pyc

# Show help
help:
	@echo "House Judiciary Committee Hearing Analysis"
	@echo ""
	@echo "Available commands:"
	@echo "  make install                     - Install Python dependencies"
	@echo "  make judiciary LAST_NAME=<name>  - Run full analysis (scrape + attendance)"
	@echo "  make scrape                      - Run comprehensive scraper (ALL hearings)"
	@echo "  make scrape-legacy               - Run legacy scraper (5 hearings only)"
	@echo "  make scrape-batch BATCH_SIZE=<n> - Run scraper with custom batch size"
	@echo "  make attendance LAST_NAME=<name> - Generate only attendance record"
	@echo "  make clean                       - Remove generated files"
	@echo "  make help                        - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make judiciary LAST_NAME=Jordan"
	@echo "  make scrape                      # Process ALL hearings"
	@echo "  make scrape-legacy               # Process only 5 hearings"
	@echo "  make scrape-batch BATCH_SIZE=20  # Process with batch size 20"
	@echo "  make attendance LAST_NAME=Raskin"

# Declare phony targets
.PHONY: install judiciary scrape scrape-legacy scrape-batch attendance clean help
