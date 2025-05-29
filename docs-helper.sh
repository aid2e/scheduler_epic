#!/bin/bash

# Simplified script for working with the Scheduler for AID2E documentation

# Function to display usage information
show_help() {
    echo "Scheduler for AID2E Documentation Helper Script"
    echo ""
    echo "Usage:"
    echo "  $0 [command]"
    echo ""
    echo "Commands:"
    echo "  serve         Start the documentation server locally"
    echo "  build         Build the documentation site"
    echo "  deploy        Deploy the documentation to GitHub Pages"
    echo "  setup         Install required dependencies"
    echo "  help          Show this help message"
    echo ""
}

# Function to install dependencies
setup() {
    echo "Installing documentation dependencies..."
    pip install -r docs/requirements-docs.txt
    echo "Dependencies installed successfully!"
}

# Function to serve documentation locally
serve() {
    echo "Starting local documentation server..."
    mkdocs serve
}

# Function to build documentation
build() {
    echo "Building documentation..."
    mkdocs build
    echo "Documentation built successfully!"
}

# Function to deploy documentation
deploy() {
    echo "Deploying documentation to GitHub Pages..."
    mkdocs gh-deploy --force --clean
    echo "Documentation deployed successfully!"
}

# Main script logic
case "$1" in
    serve)
        serve
        ;;
    build)
        build
        ;;
    deploy)
        deploy
        ;;
    setup)
        setup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
