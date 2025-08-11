#!/usr/bin/env python3
import asyncio
import tempfile
import os
import subprocess

async def test_conversion():
    # Create a test SVG
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <rect x="50" y="50" width="412" height="412" fill="#ff6b6b" stroke="#333" stroke-width="4" rx="50"/>
  <circle cx="256" cy="200" r="60" fill="#ffffff"/>
  <rect x="200" y="300" width="112" height="40" fill="#333" rx="20"/>
</svg>'''
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as svg_file:
        svg_file.write(svg_content.encode())
        svg_path = svg_file.name
    
    with tempfile.NamedTemporaryFile(suffix='.tgs', delete=False) as tgs_file:
        tgs_path = tgs_file.name
    
    try:
        # Test the exact command our bot uses
        lottie_convert_path = "/home/runner/workspace/.pythonlibs/bin/lottie_convert.py"
        cmd = [
            'python', lottie_convert_path,
            svg_path,
            tgs_path,
            '--sanitize',
            '--width', '512',
            '--height', '512',
            '--fps', '30'
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        print(f"Return code: {process.returncode}")
        print(f"Stdout: {stdout.decode('utf-8')}")
        print(f"Stderr: {stderr.decode('utf-8')}")
        
        if os.path.exists(tgs_path):
            size = os.path.getsize(tgs_path)
            print(f"TGS file created: {tgs_path} ({size} bytes)")
            
            # Check if it's a valid gzipped file
            try:
                with open(tgs_path, 'rb') as f:
                    data = f.read()
                    print(f"First 20 bytes: {data[:20].hex()}")
            except Exception as e:
                print(f"Error reading TGS file: {e}")
        else:
            print("No TGS file was created")
            
    finally:
        # Cleanup
        try:
            os.unlink(svg_path)
            os.unlink(tgs_path)
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_conversion())