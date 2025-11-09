# mytool

A command-line tool to automate the generation and management of `README.md` files across a collection of projects, enabling seamless two-way synchronization with a central notes repository (like Obsidian).

## Features

- **Project Scaffolding**: Quickly create or delete projects from the command line.
- **Automated README Generation**: Automatically generates and updates a `README.md` for each project, including YAML front-matter and a file structure tree.
- **Content Preservation**: Updates `README.md` files without overwriting user-added content.
- **Two-Way Synchronization**:
  - **Collect**: Gathers all project `README.md` files into a central notes directory, converting file links to absolute paths for global access.
  - **Distribute**: Pushes changes from the notes directory back to the individual projects, converting links back to relative paths.
- **Conflict Handling**: Detects and flags content conflicts during the synchronization process.
- **Interactive Configuration**: Guides the user through an initial setup to configure project and notes directories.

## Installation

1.  Clone the repository:
    ```bash
    git clone <your-repo-url>
    cd projecter
    ```

2.  Install the package in editable mode:
    ```bash
    pip install -e .
    ```
    This makes the `projecter` command available in your shell.

## Usage

The tool is invoked using the `projecter` command.

### First-Time Setup

On the first run, the tool will prompt you to configure the necessary paths:
1.  **Project root directory**: The folder containing all your individual project subdirectories.
2.  **Notes directory**: The central folder (e.g., your Obsidian vault) where READMEs will be synced.

```bash
projecter
```

### Commands

#### Configuration

-   **Change existing configuration**:
    ```bash
    projecter change-config
    ```

#### Project Management

-   **Create a new project**:
    ```bash
    projecter new <project-name>
    ```
    This creates a new folder and a basic `README.md` inside your project root directory.

-   **Delete a project**:
    ```bash
    projecter delete <project-name>
    ```

#### Synchronization

-   **Run the full sync cycle**:
    ```bash
    projecter sync
    ```
    This command runs the following three steps in sequence:
    1.  **`project`**: Updates the file tree and front-matter in every project's `README.md`.
    2.  **`collect`**: Syncs content from all projects *to* the notes directory.
    3.  **`distribute`**: Syncs content *from* the notes directory back to the projects.

### How the Sync Process Works

1.  **`projecter sync`** is executed.
2.  The tool scans the project directory, updating each `README.md` with a correct file tree and ensuring it has the required `project` and `tags` front-matter.
3.  It then **collects** all `README.md` files, converts their internal links to absolute paths, and saves them as `!project-name.md` in your notes directory.
4.  After you make changes in your notes directory, running `projecter sync` again will **distribute** those changes back to the original `README.md` files in each project, converting the links back to relative paths.
