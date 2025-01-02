# Running PanelGeneMapper in Docker

## Prerequisites

To install and run **PanelGeneMapper** via Docker, ensure that Docker is installed on your system. Refer to [Docker's documentation](https://docs.docker.com/get-docker/) for installation instructions.

---

## Clone the Repository

Create a directory for your project repositories and move into it. Clone the **PanelGeneMapper** repository:

```bash
$ git clone https://github.com/Miladeb77/Y2_Genepanel_project.git
```

Navigate into the project directory:

```bash
$ cd Y2_Genepanel_project
```

If you have cloned the repository previously, ensure it is up to date:

```bash
$ git pull
```

---

## Build and Start the Docker Container

### Create Required Directories

Create directories to share resources between your local machine and the Docker container:

```bash
$ mkdir -p ~/Y2_Genepanel_project/databases ~/Y2_Genepanel_project/logs ~/Y2_Genepanel_project/output
```

### Build the Docker Image

Build the Docker image using the provided `Dockerfile`:

```bash
$ docker build -t genepanel-app .
```

You should see output similar to:

```
 => exporting to image                                                                                                                                                                                         3.8s 
 => => exporting layers                                                                                                                                                                                        3.7s 
 => => writing image sha256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx                                                                                                                   0.0s 
 => => naming to docker.io/library/genepanel-app
```

### Test the Docker Build

Run a few commands to verify that the Docker image is functioning as expected:

1. Run the test suite using PyTest (all tests should pass):

    ```bash
    $ docker run --rm -it genepanel-app pytest /app/tests/
    ```

2. List the files inside the Docker container:

    ```bash
    $ docker run --rm -it genepanel-app ls
    ```

3. Check the PanelGeneMapper help message:

    ```bash
    $ docker run --rm -it genepanel-app python PanelGeneMapper/panelgenemapper.py --help
    ```

---

## Running the Application

### Start the Container in Detached Mode

Run the container in the background:

```bash
$ docker run --rm -it --name genepanel-container -v ~/Y2_Genepanel_project/output:/app/output genepanel-app
```

Replace `~/Y2_Genepanel_project/output` with the appropriate path for your environment if necessary.

---

## Common Errors and Solutions

### Port Conflicts

If a port conflict occurs (e.g., `Ports are not available: listen tcp 0.0.0.0:8000`), modify the Docker command or `Dockerfile` to use a different port. For example, specify port 8080 instead of 8000:

- Update the command in `Dockerfile`:

    ```dockerfile
    CMD ["python", "PanelGeneMapper/panelgenemapper.py", "--port", "8080"]
    ```

- Run the container with the updated configuration:

    ```bash
    $ docker run -p 8080:8080 --rm -it genepanel-app
    ```

---

## Developing PanelGeneMapper in Docker

For development, create a new branch for your changes:

```bash
$ git checkout -b my-feature-branch
```

Run the application inside the Docker container to test your changes:

```bash
$ docker run --rm -it -v $(pwd):/app genepanel-app
```

---

## Updating PanelGeneMapper

To rebuild and update the container:

```bash
$ docker build -t genepanel-app .
```

If needed, stop any running instances:

```bash
$ docker stop genepanel-container
```

---

## Deleting Docker Resources

To clean up Docker containers and images:

- Remove specific containers:

    ```bash
    $ docker rm genepanel-container
    ```

- Remove all unused containers and images:

    ```bash
    $ docker system prune -a --volumes
    ```

Ensure the container has been removed:

```bash
$ docker ps
```

Stop any remaining containers:

```bash
$ docker stop <container_id>
