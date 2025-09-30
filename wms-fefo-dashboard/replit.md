# WMS FEFO Dashboard

## Overview
This is a single-screen Flask-based dashboard for analyzing FEFO (First Expired, First Out) inventory violations from SAP extracts. The application processes LT22 and LX03 files to generate comprehensive analytics, visualizations, and pick priority lists.

## Project Structure
- **app.py**: Main Flask application with data processing logic
- **templates/**: HTML templates (dashboard.html, layout.html)
- **static/**: CSS styles (AS/400 green-on-black theme)
- **app_data/**: Runtime directory for uploaded files, generated charts, and analysis results
- **requirements.txt**: Python dependencies

## Technology Stack
- **Backend**: Flask (Python 3.11)
- **Data Processing**: pandas, openpyxl
- **Visualization**: matplotlib
- **Production Server**: gunicorn

## Key Features
- Upload SAP LT22 and LX03 Excel files
- Real-time FEFO violation analysis
- Visual charts (violations by storage type, inventory by expiry buckets)
- Detailed tables (top materials, bins, users with violations)
- Export pick priority CSV (Material → SLED/BBD → Batch)
- AS/400-inspired green-on-black terminal aesthetic

## Development Setup
The application is configured to run on:
- **Host**: 0.0.0.0 (required for Replit proxy)
- **Port**: 5000
- **Debug Mode**: Enabled in development

## Deployment Configuration
- **Target**: Autoscale (stateless web app)
- **Production Server**: gunicorn with reuse-port flag
- **Command**: `gunicorn --bind=0.0.0.0:5000 --reuse-port app:app`

## Recent Changes (September 30, 2025)
- Extracted project from zip archive
- Installed Python 3.11 and all dependencies
- Configured Flask workflow for Replit environment
- Set up deployment configuration with gunicorn
- Updated .gitignore for Python project
- Cleaned up requirements.txt (removed duplicates, added gunicorn)

## User Preferences
None specified yet.

## Architecture Notes
- The app uses Flask's built-in development server for local/dev environment
- For production deployment, gunicorn is used as the WSGI server
- All generated files (charts, CSVs, JSON) are stored in app_data/ directory
- The application is stateless - all data comes from uploaded files
