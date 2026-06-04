"""
RocketRide EaaS (Engine as a Service) Entry Point
This script is automatically launched by the RocketRide engine.
"""

import sys
import asyncio
import os
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(project_root / ".env")


async def main():
    """
    Initialize and run the RocketRide Engine as a Service.
    This serves as the entry point for the local RocketRide DAP server.
    """
    try:
        # Import RocketRide client after env is loaded
        from rocketride import RocketRideClient
        
        # Initialize the client (reads config from .env)
        client = RocketRideClient()
        
        # Connect to the RocketRide DAP server
        await client.connect()
        
        # Keep the service running to maintain the DAP connection
        # The engine will manage the actual lifecycle
        print("RocketRide EaaS initialized and ready", file=sys.stderr)
        sys.stderr.flush()
        
        # Stay alive indefinitely - the engine manages shutdown
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"RocketRide EaaS failed to initialize: {e}", file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)
    finally:
        try:
            await client.disconnect()
        except:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error in RocketRide EaaS: {e}", file=sys.stderr)
        sys.exit(1)
