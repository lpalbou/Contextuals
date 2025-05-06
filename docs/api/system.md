# System Provider API

The System Provider offers contextual information about the local system, including operating system details, user information, and hardware specifications.

## Overview

The System Provider gives access to:

- Operating system information (name, version, architecture)
- Current user information (username, home directory, shell)
- Logged-in users information
- Hardware details (CPU, memory, disk)
- Network information (hostname, IP address, MAC address)

All information is local to the machine, requiring no internet connection or API keys.

## Methods

### get_system_info()

Get general information about the operating system and environment.

**Returns:**
- Dictionary with system information, including:
  - Operating system details (name, version, platform)
  - Network information (hostname, IP address)
  - Environment variables
  - Platform-specific information (Linux distribution, macOS version, Windows edition)

**Example:**
```python
from contextual_cc import ContextualCC

context = ContextualCC()
system_info = context.system.get_system_info()

print(f"OS: {system_info['data']['os']['system']} {system_info['data']['os']['version']}")
print(f"Hostname: {system_info['data']['hostname']}")
print(f"IP Address: {system_info['data']['ip_address']}")
```

**Response Structure:**
```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "system_info",
  "is_cached": false,
  "data": {
    "os": {
      "name": "posix",
      "system": "Darwin",
      "release": "21.6.0",
      "version": "Darwin Kernel Version 21.6.0",
      "platform": "macOS-12.5-x86_64-i386-64bit",
      "machine": "x86_64",
      "processor": "i386",
      "architecture": "64bit",
      "python_version": "3.10.0",
      "macos_version": "12.5"
    },
    "hostname": "macbook-pro.local",
    "ip_address": "192.168.1.100",
    "user": {
      "username": "user",
      "home_directory": "/Users/user",
      "shell": "/bin/zsh"
    },
    "environment": {
      "path": "/usr/local/bin:/usr/bin:/bin",
      "lang": "en_US.UTF-8",
      "term": "xterm-256color",
      "terminal": "iTerm.app"
    }
  }
}
```

### get_user_info()

Get information about the current user.

**Returns:**
- Dictionary with user information, including:
  - Username
  - Home directory
  - Shell
  - User ID and group ID (on Unix-like systems)
  - Full name (when available)

**Example:**
```python
from contextual_cc import ContextualCC

context = ContextualCC()
user_info = context.system.get_user_info()

print(f"Username: {user_info['data']['username']}")
print(f"Home directory: {user_info['data']['home_directory']}")
if 'full_name' in user_info['data']:
    print(f"Full name: {user_info['data']['full_name']}")
```

**Response Structure:**
```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "user_info",
  "is_cached": false,
  "data": {
    "username": "user",
    "home_directory": "/Users/user",
    "shell": "/bin/zsh",
    "language": "en_US.UTF-8",
    "terminal": "iTerm.app",
    "uid": 501,
    "gid": 20,
    "full_name": "Example User"
  }
}
```

### get_machine_info()

Get detailed information about the local machine's hardware and system configuration.

**Returns:**
- Dictionary with detailed machine information, including:
  - System identification (hostname, architecture, platform)
  - CPU information (model, cores, processors)
  - Memory details (total, used, free)
  - Disk information (total, used, free)
  - Network details (IP address, MAC address)
  - Hardware identifiers (UUID when available)

**Example:**
```python
from contextual_cc import ContextualCC

context = ContextualCC()
machine_info = context.system.get_machine_info()

print(f"Hostname: {machine_info['data']['hostname']}")
print(f"System: {machine_info['data']['system']} {machine_info['data']['release']}")
print(f"Architecture: {machine_info['data']['architecture']}")

if 'cpu' in machine_info['data']:
    print(f"\nCPU: {machine_info['data']['cpu'].get('model', 'Unknown')}")
    print(f"Cores: {machine_info['data']['cpu'].get('cores', 'Unknown')}")

if 'memory' in machine_info['data']:
    memory = machine_info['data']['memory']
    print(f"\nMemory: {memory.get('total_mb', 'Unknown')} MB total")
    print(f"Memory usage: {memory.get('usage_percent', 'Unknown')}%")

if 'disk' in machine_info['data']:
    disk = machine_info['data']['disk']
    print(f"\nDisk: {disk.get('total_gb', 'Unknown')} GB total")
    print(f"Disk usage: {disk.get('usage_percent', 'Unknown')}%")
```

**Response Structure:**
```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "machine_info",
  "is_cached": false,
  "data": {
    "hostname": "macbook-pro.local",
    "fqdn": "macbook-pro.local",
    "architecture": "64bit",
    "machine": "x86_64",
    "processor": "i386",
    "system": "Darwin",
    "release": "21.6.0",
    "version": "Darwin Kernel Version 21.6.0",
    "platform": "macOS-12.5-x86_64-i386-64bit",
    "python_version": "3.10.0",
    "ip_address": "192.168.1.100",
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "hardware_uuid": "12345678-9ABC-DEF0-1234-56789ABCDEF0",
    "system_info": {
      "system": "Darwin",
      "node": "macbook-pro.local",
      "release": "21.6.0",
      "version": "Darwin Kernel Version 21.6.0",
      "machine": "x86_64",
      "processor": "i386",
      "architecture": "64bit"
    },
    "cpu": {
      "physical_processors": 1,
      "cores": 8,
      "logical_processors": 8,
      "model": "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz"
    },
    "memory": {
      "total_mb": 16384,
      "free_mb": 4096,
      "used_mb": 12288,
      "usage_percent": 75.0
    },
    "disk": {
      "total_gb": 500.0,
      "free_gb": 200.0,
      "used_gb": 300.0,
      "usage_percent": 60.0
    }
  }
}
```

### get_logged_users()

Get information about all users currently logged into the system.

**Returns:**
- Dictionary with information about logged users, including:
  - Current user details
  - List of all logged users
  - Total count of logged users
  - User names and full names when available

**Example:**
```python
from contextual_cc import ContextualCC

context = ContextualCC()
users_info = context.system.get_logged_users()

print(f"Current user: {users_info['data']['current_user']}")
print(f"Total users logged in: {users_info['data']['total_user_count']}")

print("\nAll logged users:")
for user in users_info['data']['all_logged_users']:
    user_display = user['username']
    if 'full_name' in user and user['full_name']:
        user_display += f" ({user['full_name']})"
    print(f"- {user_display}")
```

**Response Structure:**
```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "logged_users",
  "is_cached": false,
  "data": {
    "current_user": "user",
    "current_user_info": {
      "uid": 501,
      "gid": 20,
      "full_name": "Example User",
      "home_directory": "/Users/user",
      "shell": "/bin/zsh"
    },
    "all_logged_users": [
      {
        "username": "user",
        "uid": 501,
        "full_name": "Example User"
      },
      {
        "username": "otheruser",
        "uid": 502,
        "full_name": "Other User"
      }
    ],
    "total_user_count": 2
  }
}
```

## Platform-Specific Notes

The System Provider works on all major platforms with graceful feature degradation:

### Linux

- Full hardware information including CPU, memory, disk usage
- Detailed OS information including distribution details
- Complete user and group information

### macOS

- Comprehensive system information
- Detailed hardware specifications
- Excellent user information coverage

### Windows

- Basic system information is always available
- Some hardware details require administrative privileges
- Command prompt window might briefly appear when collecting detailed information

## Error Handling

The System Provider is designed to gracefully handle errors:

- If a specific piece of information is unavailable, its field will be omitted or marked as "Unknown"
- No exceptions will be thrown if hardware information cannot be retrieved
- Default values will be used for critical fields that cannot be determined

## Caching Behavior

The System Provider uses caching to minimize resource usage:

- `get_system_info()`: Cached for 1 hour (3600 seconds)
- `get_user_info()`: Cached for 1 minute (60 seconds)
- `get_machine_info()`: Cached for 1 minute (60 seconds)
- `get_logged_users()`: Cached for 1 minute (60 seconds)

The cache duration can be modified by adjusting the global cache settings when initializing the library:

```python
from contextual_cc import ContextualCC

# Set a custom cache duration for all providers
context = ContextualCC(cache_duration=120)  # 2 minutes
```