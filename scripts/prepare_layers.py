import os
import shutil
import site
import sys
from pathlib import Path

def get_site_packages_from_venv():
    """Get the site-packages directory from the current virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # We're in a virtual environment
        return [p for p in site.getsitepackages() if 'site-packages' in p][0]
    raise Exception("No virtual environment detected. Please activate your .venv first.")

def copy_dependencies():
    """Copy required packages from venv to layers directory."""
    # Paths
    root_dir = Path(__file__).parent.parent
    requirements_file = root_dir / 'layers' / 'requirements.txt'
    layers_dir = root_dir / 'layers' / 'python'
    
    # Ensure the layers directory exists and is empty
    if layers_dir.exists():
        shutil.rmtree(layers_dir)
    layers_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the site-packages directory from venv
    site_packages = Path(get_site_packages_from_venv())
    
    # Read requirements file
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Copy each package
    for requirement in requirements:
        package_name = requirement.split('==')[0].split('>=')[0].split('<=')[0].strip()
        
        # Look for either the package directory or the .dist-info directory
        package_dir = site_packages / package_name
        if not package_dir.exists():
            package_dir = site_packages / f"{package_name.replace('-', '_')}"
        
        if package_dir.exists():
            # Copy package directory
            dest_dir = layers_dir / package_dir.name
            if package_dir.is_dir():
                shutil.copytree(package_dir, dest_dir)
            else:
                shutil.copy2(package_dir, dest_dir)
            
            # Copy associated .dist-info directory if it exists
            dist_info = list(site_packages.glob(f"{package_name}*.dist-info"))
            if dist_info:
                shutil.copytree(dist_info[0], layers_dir / dist_info[0].name)
        else:
            print(f"Warning: Package {package_name} not found in site-packages")

if __name__ == '__main__':
    try:
        copy_dependencies()
        print("Successfully copied dependencies to layers/python/")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)