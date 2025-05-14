import os
import shutil
import site
import sys
from pathlib import Path

def get_site_packages_from_venv():
    """Get the site-packages directory from the current virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # Primero intentamos obtener del entorno virtual activo
        venv_paths = [p for p in site.getsitepackages() if 'site-packages' in p]
        if venv_paths:
            return venv_paths[0]
        
        # Si no encontramos, buscamos en la estructura típica de .venv
        root_dir = Path(__file__).parent.parent
        possible_paths = [
            root_dir / '.venv' / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages',
            root_dir / '.venv' / 'Lib' / 'site-packages',  # Para Windows
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
                
        raise Exception("Could not find site-packages directory in .venv")
    raise Exception("No virtual environment detected. Please activate your .venv first.")

def validate_requirements_file(requirements_file):
    """Validate that the requirements file exists and is not empty."""
    if not requirements_file.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_file}")
    
    if requirements_file.stat().st_size == 0:
        raise ValueError("Requirements file is empty")

def parse_package_name(requirement):
    """Parse package name from requirement string."""
    # Remove any whitespace and comments
    requirement = requirement.split('#')[0].strip()
    if not requirement:
        return None
    
    # Handle different requirement formats
    for operator in ['==', '>=', '<=', '>', '<', '~=', '!=']:
        if operator in requirement:
            return requirement.split(operator)[0].strip()
    
    return requirement

def find_package_directory(site_packages, package_name):
    """Find the correct package directory trying different name variations."""
    # Mapping for packages with different install names
    package_mapping = {
        'PyJWT': 'jwt',
        'python-dateutil': 'dateutil'
    }
    
    # Check if we have a special mapping for this package
    if package_name in package_mapping:
        package_name = package_mapping[package_name]
    
    possible_names = [
        package_name,
        package_name.lower(),
        package_name.replace('-', '_'),
        package_name.replace('-', '_').lower(),
    ]
    
    for name in possible_names:
        package_dir = site_packages / name
        if package_dir.exists():
            return package_dir
            
    # Buscar de forma más flexible usando glob
    for name in possible_names:
        matches = list(site_packages.glob(f"{name}*"))
        matches = [m for m in matches if m.is_dir() and not m.name.endswith('.dist-info')]
        if matches:
            return matches[0]
    
    return None

def copy_dependencies():
    """Copy required packages from venv to layers directory."""
    # Paths
    root_dir = Path(__file__).parent.parent
    requirements_file = root_dir / 'layers' / 'requirements.txt'
    layers_dir = root_dir / 'layers' / 'python'
    
    # Validate requirements file
    validate_requirements_file(requirements_file)
    
    # Ensure the layers directory exists
    layers_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the site-packages directory from venv
    site_packages = Path(get_site_packages_from_venv())
    print(f"Using site-packages directory: {site_packages}")
    
    # Read and validate requirements file
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not requirements:
        raise ValueError("No valid requirements found in requirements.txt")
    
    successful_copies = []
    failed_copies = []
    
    # Copy each package
    for requirement in requirements:
        try:
            package_name = parse_package_name(requirement)
            if not package_name:
                continue
            
            print(f"\nProcessing package: {package_name}")
            
            # Look for the package directory
            package_dir = find_package_directory(site_packages, package_name)
            
            if package_dir:
                print(f"Found package directory: {package_dir}")
                # Copy package directory
                dest_dir = layers_dir / package_dir.name
                if dest_dir.exists():
                    if dest_dir.is_dir():
                        shutil.rmtree(dest_dir)
                    else:
                        dest_dir.unlink()
                
                if package_dir.is_dir():
                    shutil.copytree(package_dir, dest_dir)
                else:
                    shutil.copy2(package_dir, dest_dir)
                
                # Copy associated .dist-info directory if it exists
                # Try different patterns for dist-info
                dist_info = None
                patterns = [
                    f"{package_name}*.dist-info",
                    f"{package_name.lower()}*.dist-info",
                    "PyJWT*.dist-info" if package_name == "jwt" else None,  # Special case for PyJWT
                    f"{package_dir.name}*.dist-info"  # Use the actual directory name
                ]
                patterns = [p for p in patterns if p]  # Remove None values
                
                for pattern in patterns:
                    print(f"Looking for dist-info with pattern: {pattern}")
                    matches = list(site_packages.glob(pattern))
                    if matches:
                        dist_info = matches[0]
                        break
                
                if dist_info:
                    print(f"Found dist-info: {dist_info}")
                    dist_info_dest = layers_dir / dist_info.name
                    if dist_info_dest.exists():
                        shutil.rmtree(dist_info_dest)
                    shutil.copytree(dist_info, dist_info_dest)
                else:
                    print(f"No dist-info found for {package_name}")
                
                successful_copies.append(package_name)
            else:
                print(f"Package directory not found for {package_name}")
                # List contents of site-packages for debugging
                print("Available packages in site-packages:")
                for item in site_packages.iterdir():
                    if item.is_dir() and not item.name.endswith('.dist-info'):
                        print(f"  - {item.name}")
                failed_copies.append(package_name)
        
        except Exception as e:
            failed_copies.append(package_name)
            print(f"Error processing {package_name}: {str(e)}")
    
    # Report results
    if successful_copies:
        print("\nSuccessfully copied packages:")
        for package in successful_copies:
            print(f"  - {package}")
    
    if failed_copies:
        print("\nFailed to copy packages:")
        for package in failed_copies:
            print(f"  - {package}")
        
        if not successful_copies:
            raise Exception("No packages were successfully copied")

if __name__ == '__main__':
    try:
        copy_dependencies()
        print("Successfully copied dependencies to layers/python/")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)