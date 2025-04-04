import os
import zipfile
import tempfile
import shutil
import traceback
import argparse # For command-line arguments
import fnmatch # For wildcard pattern matching (exclusions)

def generate_repository_description(zip_path, output_txt_path, exclude_patterns=None, max_file_size_kb=None, verbose=False):
    """
    Unpacks the repository from a .zip file, creates a directory structure listing,
    and adds the content of all text files (respecting exclusions and size limits)
    into a single .txt file. Skips the content of binary files.

    Args:
        zip_path (str): Path to the .zip file containing the repository.
        output_txt_path (str): Path where the output .txt file will be saved.
        exclude_patterns (list, optional): List of glob patterns for files/dirs to exclude. Defaults to None.
        max_file_size_kb (int, optional): Maximum size (in KB) for a file's content to be included. Defaults to None (no limit).
        verbose (bool, optional): If True, enables detailed logging. Defaults to False.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    if exclude_patterns is None:
        exclude_patterns = []

    # --- 1. Input file path validation ---
    if not os.path.exists(zip_path):
        print(f"Error: Input file '{zip_path}' does not exist.")
        return False
    if not zip_path.lower().endswith('.zip'):
        print(f"Error: The provided file '{os.path.basename(zip_path)}' is not a .zip file.")
        return False

    if verbose:
        print(f"Processing file: {os.path.basename(zip_path)}")
        print(f"Output file: {output_txt_path}")
        if exclude_patterns:
            print(f"Exclusion patterns: {exclude_patterns}")
        if max_file_size_kb is not None and max_file_size_kb > 0:
            print(f"Max file size limit: {max_file_size_kb} KB")
        else:
             print("No file size limit.")


    # Convert max size to bytes if specified
    max_size_bytes = (max_file_size_kb * 1024) if max_file_size_kb is not None and max_file_size_kb > 0 else None

    # Use a temporary directory that will be automatically deleted
    try:
        with tempfile.TemporaryDirectory(prefix="repo_analyzer_") as temp_dir:
            if verbose:
                print(f"Unpacking archive to temporary directory: {temp_dir}...")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                if verbose:
                    print("Unpacking finished.")
            except zipfile.BadZipFile:
                print(f"Error: File '{os.path.basename(zip_path)}' is not a valid ZIP archive or is corrupted.")
                return False
            except Exception as e:
                print(f"\nError: An unexpected error occurred while unpacking the archive: {e}")
                traceback.print_exc()
                return False

            # --- 4. Identify the main repository directory inside the ZIP ---
            # (Logic remains largely the same, added verbose logging)
            extracted_items = os.listdir(temp_dir)
            repo_root_in_temp = temp_dir
            base_name_zip = os.path.splitext(os.path.basename(zip_path))[0] # Get name from zip
            repo_display_name = base_name_zip # Default display name

            potential_dirs = [
                d for d in extracted_items
                if os.path.isdir(os.path.join(temp_dir, d)) and not d.startswith('.')
            ]

            if len(potential_dirs) == 1:
                 repo_root_in_temp = os.path.join(temp_dir, potential_dirs[0])
                 repo_display_name = potential_dirs[0]
                 if verbose:
                    print(f"Found single main repository directory in archive: '{repo_display_name}'")
            elif len(potential_dirs) > 1 :
                 print("Warning: Found multiple directories at the top level in the archive.")
                 print("Assuming archive root as the main repository directory.")
                 # repo_display_name remains base_name_zip
            else:
                 is_flat_structure = any(os.path.isfile(os.path.join(temp_dir, item)) for item in extracted_items)
                 if is_flat_structure:
                     print("Warning: Looks like a flat file structure in the archive.")
                 else:
                     print("Warning: Could not find a main directory in the archive (maybe empty?).")
                 print("Assuming archive root as the main repository directory.")
                 # repo_display_name remains base_name_zip

            if verbose:
                print(f"Effective repository root for processing: {repo_root_in_temp}")

            # --- 5. Prepare for writing the output file ---
            output_lines = []
            output_lines.append(f"Repository structure and content from file: {os.path.basename(zip_path)}\n")
            if exclude_patterns:
                output_lines.append(f"Applied exclusion patterns: {', '.join(exclude_patterns)}\n")
            if max_size_bytes is not None:
                 output_lines.append(f"Applied max file size limit: {max_file_size_kb} KB\n")
            output_lines.append("=" * 80 + "\n")

            # --- 6. Generate directory structure ---
            output_lines.append("DIRECTORY STRUCTURE:\n")
            output_lines.append("-" * 80 + "\n")

            structure_lines = []
            files_to_process = [] # List of tuples: (relative_path_for_display, absolute_path_for_reading)
            total_dirs = 0
            total_files = 0
            excluded_dirs_count = 0
            excluded_files_count = 0

            # --- Exclusion Helper Function ---
            def is_excluded(path_to_check, relative_to):
                """Checks if a given path matches any exclusion patterns."""
                if not exclude_patterns:
                    return False
                # Use relative path for matching patterns
                relative_path_for_match = os.path.relpath(path_to_check, relative_to).replace(os.sep, '/')
                for pattern in exclude_patterns:
                    # Match against the full relative path or just the basename
                    if fnmatch.fnmatch(relative_path_for_match, pattern) or \
                       fnmatch.fnmatch(os.path.basename(path_to_check), pattern):
                        if verbose:
                            print(f"  Excluding '{relative_path_for_match}' due to pattern '{pattern}'")
                        return True
                return False

            # --- Walk the Directory Tree ---
            # Use a list to store items for processing to allow modification during iteration
            items_to_walk = list(os.walk(repo_root_in_temp, topdown=True))

            for root, dirs, files in items_to_walk:
                # Check if the current root directory itself should be excluded
                if is_excluded(root, repo_root_in_temp) and root != repo_root_in_temp:
                     excluded_dirs_count += 1 + len(dirs) # Count this dir and all potential subdirs
                     excluded_files_count += len(files)
                     dirs[:] = [] # Don't descend into subdirectories
                     files[:] = [] # Don't process files in this directory
                     continue # Skip processing this directory further

                # Calculate display paths and level
                relative_path = os.path.relpath(root, repo_root_in_temp)
                relative_path_display = relative_path.replace(os.sep, '/')

                if relative_path == '.':
                    level = 0
                    structure_lines.append(f"{repo_display_name}/\n")
                    total_dirs += 1
                else:
                    level = relative_path.count(os.sep) + 1
                    indent = '  ' * level + '|-- '
                    structure_lines.append(f"{indent}{os.path.basename(root)}/\n")
                    total_dirs += 1

                file_indent = '  ' * (level + 1) + '|-- '

                # --- Filter Directories ---
                original_dirs = list(dirs) # Keep original list for counting exclusions
                dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d), repo_root_in_temp)]
                excluded_dirs_count += len(original_dirs) - len(dirs)

                # --- Filter Files ---
                original_files = list(files) # Keep original list for counting exclusions
                filtered_files = []
                for f in files:
                    full_path = os.path.join(root, f)
                    if not is_excluded(full_path, repo_root_in_temp):
                        filtered_files.append(f)
                    else:
                        excluded_files_count += 1
                files[:] = filtered_files # Update files list for processing below

                # Sort remaining dirs and files
                dirs.sort()
                files.sort()

                # Process filtered files
                for f in files:
                    structure_lines.append(f"{file_indent}{f}\n")
                    total_files += 1
                    full_file_path = os.path.join(root, f)

                    if relative_path == '.':
                         relative_file_path_header = f
                    else:
                         relative_file_path_header = os.path.join(relative_path_display, f).replace(os.sep, '/')

                    files_to_process.append((relative_file_path_header, full_file_path))

            output_lines.extend(structure_lines)
            output_lines.append(f"\n(Included directories: {total_dirs}, Included files: {total_files}")
            if excluded_dirs_count > 0 or excluded_files_count > 0:
                 output_lines.append(f", Excluded dirs: {excluded_dirs_count}, Excluded files: {excluded_files_count}")
            output_lines.append(")\n")
            output_lines.append("\n" + "=" * 80 + "\n")

            # --- 7. Add file contents ---
            output_lines.append("FILE CONTENTS:\n")
            output_lines.append("-" * 80 + "\n\n")

            if verbose:
                print(f"Processing content of {len(files_to_process)} included files...")
            processed_files = 0
            skipped_binary = 0
            skipped_size = 0
            read_errors = 0

            for rel_path_header, full_path in files_to_process:
                processed_files += 1
                output_lines.append(f"--- BEGIN FILE: {rel_path_header} ---\n")

                # --- File Size Check ---
                try:
                    file_size = os.path.getsize(full_path)
                    if max_size_bytes is not None and file_size > max_size_bytes:
                        output_lines.append(f"[File content skipped - size ({file_size / 1024:.1f} KB) exceeds limit ({max_file_size_kb} KB)]\n")
                        skipped_size += 1
                        output_lines.append(f"\n--- END FILE: {rel_path_header} ---\n\n")
                        if verbose: print(f"  Skipping '{rel_path_header}' due to size.")
                        continue # Skip to next file
                except OSError as e_size:
                    output_lines.append(f"[Error checking file size: {e_size}]\n")
                    read_errors += 1 # Count as a read error type
                    output_lines.append(f"\n--- END FILE: {rel_path_header} ---\n\n")
                    continue

                # --- Binary Check ---
                is_binary = False
                try:
                    with open(full_path, 'rb') as fb:
                        chunk = fb.read(1024)
                        if b'\0' in chunk:
                            is_binary = True
                            skipped_binary += 1
                except (IOError, OSError) as e_bin_check:
                    output_lines.append(f"[Error checking if file is binary: {e_bin_check}]\n")
                    read_errors += 1
                    output_lines.append(f"\n--- END FILE: {rel_path_header} ---\n\n")
                    continue
                except Exception as e_bin_check_other:
                    output_lines.append(f"[Unexpected error checking if file is binary: {e_bin_check_other}]\n")
                    read_errors += 1
                    output_lines.append(f"\n--- END FILE: {rel_path_header} ---\n\n")
                    continue

                if is_binary:
                    output_lines.append(f"[Binary file - content skipped]\n")
                    if verbose: print(f"  Skipping '{rel_path_header}' as binary.")
                else:
                    # --- Read Text Content ---
                    if verbose: print(f"  Reading '{rel_path_header}'...")
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                        output_lines.append(content)
                    except UnicodeDecodeError:
                        if verbose: print(f"    UTF-8 failed for '{rel_path_header}', trying Latin-1...")
                        try:
                            with open(full_path, 'r', encoding='latin-1') as f_latin:
                                content = f_latin.read()
                            output_lines.append("[WARNING: Could not read as UTF-8, read as Latin-1]\n")
                            output_lines.append(content)
                        except Exception as e_fallback:
                            output_lines.append(f"[Error reading file (tried UTF-8, Latin-1): {e_fallback}]\n")
                            read_errors += 1
                    except (IOError, OSError) as e_read:
                        output_lines.append(f"[Error reading file: {e_read}]\n")
                        read_errors += 1
                    except Exception as e_read_other:
                        output_lines.append(f"[Unexpected error reading file: {e_read_other}]\n")
                        read_errors += 1

                output_lines.append(f"\n--- END FILE: {rel_path_header} ---\n\n")

                # Progress indicator (less intrusive without verbose)
                if not verbose and (processed_files % 20 == 0 or processed_files == len(files_to_process)):
                     print(f"  Processed {processed_files}/{len(files_to_process)} files...", end='\r')

            # Clear progress line
            print(" " * 70, end='\r')
            if verbose:
                print("File content processing finished.")
            else:
                print("File processing finished.")


            # --- 8. Save the result to the .txt file ---
            if verbose:
                print(f"Saving result to file '{output_txt_path}'...")
            try:
                # Ensure output directory exists
                output_dir = os.path.dirname(output_txt_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    if verbose: print(f"Created output directory: {output_dir}")

                with open(output_txt_path, 'w', encoding='utf-8') as outfile:
                    outfile.write("".join(output_lines))

                print("-" * 80)
                print(f"Success! File '{output_txt_path}' has been created.")
                print(f"  Summary: Included Files: {processed_files}, Skipped Binary: {skipped_binary}, Skipped Size: {skipped_size}, Read Errors: {read_errors}")
                if excluded_files_count > 0 or excluded_dirs_count > 0:
                    print(f"           Excluded Dirs: {excluded_dirs_count}, Excluded Files: {excluded_files_count}")
                print("-" * 80)
                return True
            except IOError as e:
                print(f"\nError: Could not save the output file '{output_txt_path}'. Reason: {e}")
                return False
            except Exception as e:
                print(f"\nError: An unexpected error occurred while saving the file: {e}")
                traceback.print_exc()
                return False

    except Exception as e:
        print(f"\nError: An unexpected top-level error occurred: {e}")
        traceback.print_exc()
        # Attempt to clean up if the temporary directory was not removed automatically
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
             try:
                 if verbose: print(f"Attempting manual removal of temporary directory: {temp_dir}")
                 shutil.rmtree(temp_dir, ignore_errors=True)
             except Exception as cleanup_error:
                 print(f"Warning: Failed to remove temporary directory '{temp_dir}': {cleanup_error}")
        return False

# --- Main script execution with argument parsing ---
def main():
    """Parses command-line arguments and runs the generator."""
    parser = argparse.ArgumentParser(
        description="Generates a text file containing the directory structure and content of a code repository from a ZIP archive.",
        formatter_class=argparse.RawTextHelpFormatter # Keep help text formatting
    )

    parser.add_argument(
        "input_zip",
        help="Path to the input repository .zip file."
    )
    parser.add_argument(
        "-o", "--output",
        help="Path for the output .txt file.\nIf not provided, it defaults to '<zip_file_base_name>_structure_and_content.txt' in the current directory."
    )
    parser.add_argument(
        "-e", "--exclude",
        action="append", # Allows specifying multiple times: -e "*.log" -e "dist/"
        default=[],
        metavar="PATTERN",
        help="Glob pattern for files or directories to exclude (e.g., '*.log', 'node_modules/', 'build*').\nCan be used multiple times. Matches relative paths and basenames."
    )
    parser.add_argument(
        "-mfs", "--max-file-size",
        type=int,
        metavar="KB",
        default=None, # No limit by default
        help="Maximum size (in KB) of a file to include its content. Larger files will be skipped."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true", # Sets verbose to True if present
        help="Enable verbose output for detailed processing information."
    )

    args = parser.parse_args()

    # Determine output path if not provided
    output_path = args.output
    if not output_path:
        base_name = os.path.splitext(os.path.basename(args.input_zip))[0]
        output_path = f"{base_name}_structure_and_content.txt"

    # Run the main function
    if args.verbose:
        print("Starting Repository Description Generator...")
        print(f"Input ZIP: {args.input_zip}")
        print(f"Output TXT: {output_path}")
        if args.exclude: print(f"Exclusions: {args.exclude}")
        if args.max_file_size: print(f"Max File Size: {args.max_file_size} KB")
        print("-" * 30)


    success = generate_repository_description(
        zip_path=args.input_zip,
        output_txt_path=output_path,
        exclude_patterns=args.exclude,
        max_file_size_kb=args.max_file_size,
        verbose=args.verbose
    )

    if not success:
        print("\nProcessing failed.")
        exit(1) # Indicate error exit status
    else:
        if args.verbose:
            print("Processing completed successfully.")

if __name__ == "__main__":
    main()