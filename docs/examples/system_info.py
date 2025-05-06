"""Example of using system information features of Contextuals."""

from contextuals import Contextuals


def main():
    """Demonstrate system information features."""
    print("=== System Information Example ===\n")
    
    # Initialize the library
    context = Contextuals()
    
    # 1. Basic system information
    print("--- Basic System Information ---")
    system_info = context.system.get_system_info()
    os_info = system_info["data"]["os"]
    
    print(f"OS: {os_info['system']} {os_info['release']}")
    print(f"Version: {os_info['version']}")
    print(f"Architecture: {os_info['architecture']}")
    print(f"Python version: {os_info['python_version']}")
    print(f"Hostname: {system_info['data']['hostname']}")
    print(f"IP Address: {system_info['data']['ip_address']}")
    
    # 2. User information
    print("\n--- User Information ---")
    user_info = context.system.get_user_info()
    print(f"Username: {user_info['data']['username']}")
    print(f"Home directory: {user_info['data']['home_directory']}")
    if user_info['data'].get('shell'):
        print(f"Shell: {user_info['data']['shell']}")
    if user_info['data'].get('full_name'):
        print(f"Full name: {user_info['data']['full_name']}")
    if user_info['data'].get('language'):
        print(f"Language: {user_info['data']['language']}")
    
    # 3. Machine hardware information
    print("\n--- Hardware Information ---")
    machine_info = context.system.get_machine_info()
    print(f"System: {machine_info['data']['system']} {machine_info['data']['release']}")
    print(f"Architecture: {machine_info['data']['architecture']}")
    
    # CPU information
    if 'cpu' in machine_info['data']:
        cpu = machine_info['data']['cpu']
        print("\nCPU Information:")
        if cpu.get('model'):
            print(f"  Model: {cpu['model']}")
        if cpu.get('cores'):
            print(f"  Cores: {cpu['cores']}")
        if cpu.get('logical_processors'):
            print(f"  Logical processors: {cpu['logical_processors']}")
    
    # Memory information
    if 'memory' in machine_info['data']:
        memory = machine_info['data']['memory']
        print("\nMemory Information:")
        if memory.get('total_mb') is not None:
            print(f"  Total: {memory['total_mb']} MB")
        if memory.get('used_mb') is not None:
            print(f"  Used: {memory['used_mb']} MB")
        if memory.get('free_mb') is not None:
            print(f"  Free: {memory['free_mb']} MB")
        if memory.get('usage_percent') is not None:
            print(f"  Usage: {memory['usage_percent']:.1f}%")
    
    # Disk information
    if 'disk' in machine_info['data']:
        disk = machine_info['data']['disk']
        print("\nDisk Information:")
        if disk.get('total_gb') is not None:
            print(f"  Total: {disk['total_gb']:.1f} GB")
        if disk.get('used_gb') is not None:
            print(f"  Used: {disk['used_gb']:.1f} GB")
        if disk.get('free_gb') is not None:
            print(f"  Free: {disk['free_gb']:.1f} GB")
        if disk.get('usage_percent') is not None:
            print(f"  Usage: {disk['usage_percent']:.1f}%")
    
    # 4. Logged users information
    print("\n--- Logged Users ---")
    logged_users = context.system.get_logged_users()
    print(f"Current user: {logged_users['data']['current_user']}")
    print(f"Total users logged in: {logged_users['data']['total_user_count']}")
    
    if logged_users['data']['all_logged_users']:
        print("All logged users:")
        for user in logged_users['data']['all_logged_users']:
            user_display = user['username']
            if 'full_name' in user and user['full_name']:
                user_display += f" ({user['full_name']})"
            print(f"- {user_display}")
    
    print("\nExample completed.")


if __name__ == "__main__":
    main()