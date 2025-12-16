# Start from the official OSGeo image
# We use 'ubuntu-full' because it includes compilers and headers (libgdal-dev)
# which allow uv to compile the Python bindings for ANY Python version you test.
FROM ghcr.io/osgeo/gdal:ubuntu-full-latest

# Install uv by copying the binary from the official Astral image
# (This is the standard "best practice" way to install uv in other images)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# FIX: Suppress the hardlink warning inside Docker
ENV UV_LINK_MODE=copy

# FIX: Ensure compilation cache is used effectively
ENV UV_COMPILE_BYTECODE=1

# Copy your project
COPY . .

# Ensure the script is executable
RUN chmod +x test_all_versions.sh

# Default command
CMD ["./test_all_versions.sh"]
