# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/003_LocalRedpandaBroker.ipynb.

# %% auto 0
__all__ = ['logger', 'get_redpanda_docker_cmd', 'LocalRedpandaBroker', 'check_docker']

# %% ../../nbs/003_LocalRedpandaBroker.ipynb 1
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import *

import asyncer
import nest_asyncio

from .._components._subprocess import terminate_asyncio_process
from .._components.helpers import in_notebook
from .._components.logger import get_logger, supress_timestamps
from .._components.meta import delegates, export, patch
from .apache_kafka_broker import get_free_port, run_and_match

# %% ../../nbs/003_LocalRedpandaBroker.ipynb 3
if in_notebook():
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm

# %% ../../nbs/003_LocalRedpandaBroker.ipynb 4
logger = get_logger(__name__)

# %% ../../nbs/003_LocalRedpandaBroker.ipynb 6
def get_redpanda_docker_cmd(
    listener_port: int = 9092,
    tag: str = "v23.1.2",
    seastar_core: int = 1,
    memory: str = "1G",
    mode: str = "dev-container",
    default_log_level: str = "debug",
) -> List[str]:
    """
    Generates a Docker CLI command to start redpanda container

    Args:
        listener_port: Port on which the clients (producers and consumers) can connect
        tag: Tag of Redpanda image to use to start container
        seastar_core: Core(s) to use byt Seastar (the framework Redpanda uses under the hood)
        memory: The amount of memory to make available to Redpanda
        mode: Mode to use to load configuration properties in container
        default_log_level: Log levels to use for Redpanda
    """
    redpanda_docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--name",
        f"redpanda_{listener_port}",
        "-p",
        f"{listener_port}:{listener_port}",
        f"docker.redpanda.com/redpandadata/redpanda:{tag}",
        "redpanda",
        "start",
        "--kafka-addr",
        f"internal://0.0.0.0:9090,external://0.0.0.0:{listener_port}",
        "--advertise-kafka-addr",
        f"internal://localhost:9090,external://localhost:{listener_port}",
        "--smp",
        str(seastar_core),
        "--memory",
        memory,
        "--mode",
        mode,
        "--default-log-level",
        default_log_level,
    ]
    return redpanda_docker_cmd

# %% ../../nbs/003_LocalRedpandaBroker.ipynb 8
@export("fastkafka.testing")
class LocalRedpandaBroker:
    """LocalRedpandaBroker class, used for running unique redpanda brokers in tests to prevent topic clashing."""

    @delegates(get_redpanda_docker_cmd, keep=True)
    def __init__(
        self,
        topics: Iterable[str] = [],
        *,
        retries: int = 3,
        apply_nest_asyncio: bool = False,
        **kwargs: Dict[str, Any],
    ):
        """Initialises the LocalRedpandaBroker object

        Args:
            listener_port: Port on which the clients (producers and consumers) can connect
            tag: Tag of Redpanda image to use to start container
            seastar_core: Core(s) to use byt Seastar (the framework Redpanda uses under the hood)
            memory: The amount of memory to make available to Redpanda
            mode: Mode to use to load configuration properties in container
            default_log_level: Log levels to use for Redpanda
            topics: List of topics to create after sucessfull redpanda broker startup
            retries: Number of retries to create redpanda service
            apply_nest_asyncio: set to True if running in notebook
            port allocation if the requested port was taken
        """
        self.redpanda_kwargs = kwargs

        if "listener_port" not in self.redpanda_kwargs:
            self.redpanda_kwargs["listener_port"] = 9092  # type: ignore

        self.retries = retries
        self.apply_nest_asyncio = apply_nest_asyncio
        self.temporary_directory: Optional[TemporaryDirectory] = None
        self.temporary_directory_path: Optional[Path] = None
        self.redpanda_task: Optional[asyncio.subprocess.Process] = None
        self._is_started = False
        self.topics: Iterable[str] = topics

    @property
    def is_started(self) -> bool:
        return self._is_started

    @classmethod
    async def _check_deps(cls) -> None:
        """Prepares the environment for running redpanda brokers.
        Returns:
           None
        """
        raise NotImplementedError

    async def _start(self) -> str:
        """Starts a local redpanda broker instance asynchronously
        Returns:
           Redpanda broker bootstrap server address in string format: add:port
        """
        raise NotImplementedError

    def start(self) -> str:
        """Starts a local redpanda broker instance synchronously
        Returns:
           Redpanda broker bootstrap server address in string format: add:port
        """
        raise NotImplementedError

    def stop(self) -> None:
        """Stops a local redpanda broker instance synchronously
        Returns:
           None
        """
        raise NotImplementedError

    async def _stop(self) -> None:
        """Stops a local redpanda broker instance synchronously
        Returns:
           None
        """
        raise NotImplementedError

    def get_service_config_string(self, service: str, *, data_dir: Path) -> str:
        """Generates a configuration for a service
        Args:
            data_dir: Path to the directory where the zookeepeer instance will save data
            service: "redpanda", defines which service to get config string for
        """
        raise NotImplementedError

    async def _start_redpanda(self) -> None:
        """Start a local redpanda broker
        Returns:
           None
        """
        raise NotImplementedError

    async def _create_topics(self) -> None:
        """Create missing topics in local redpanda broker
        Returns:
           None
        """
        raise NotImplementedError

    def __enter__(self) -> str:
        return self.start()

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        self.stop()

    async def __aenter__(self) -> str:
        return await self._start()

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self._stop()

# %% ../../nbs/003_LocalRedpandaBroker.ipynb 10
async def check_docker() -> bool:
    try:
        docker_task = await run_and_match("docker", "-v", pattern="Docker version")
        return True
    except Exception as e:
        logger.debug(f"Error in check_docker() : {e}")
        return False

# %% ../../nbs/003_LocalRedpandaBroker.ipynb 12
@patch(cls_method=True)  # type: ignore
async def _check_deps(cls: LocalRedpandaBroker) -> None:
    if not await check_docker():
        raise RuntimeError(
            "Docker installation not found! Please install docker manually and retry."
        )

# %% ../../nbs/003_LocalRedpandaBroker.ipynb 15
@patch
async def _start_redpanda(self: LocalRedpandaBroker, service: str = "redpanda") -> None:
    logger.info(f"Starting {service}...")

    if self.temporary_directory_path is None:
        raise ValueError(
            "LocalRedpandaBroker._start_redpanda(): self.temporary_directory_path is None, did you initialise it?"
        )

    configs_tried: List[Dict[str, Any]] = []

    for i in range(self.retries + 1):
        configs_tried = configs_tried + [getattr(self, f"{service}_kwargs").copy()]

        redpanda_docker_cmd = get_redpanda_docker_cmd(**self.redpanda_kwargs)  # type: ignore

        try:
            service_task = await run_and_match(
                *redpanda_docker_cmd,
                capture="stderr",
                pattern="Bootstrap complete",
                timeout=30,
            )
        except Exception as e:
            logger.info(
                f"{service} startup failed, generating a new port and retrying..."
            )
            port = get_free_port()
            self.redpanda_kwargs["listener_port"] = port  # type: ignore

            logger.info(f"port={port}")
        else:
            setattr(self, f"{service}_task", service_task)
            return

    raise ValueError(f"Could not start {service} with params: {configs_tried}")


@patch
async def _create_topics(self: LocalRedpandaBroker) -> None:
    listener_port = self.redpanda_kwargs.get("listener_port", 9092)

    async with asyncer.create_task_group() as tg:
        processes = [
            tg.soonify(run_and_match)(
                "docker",
                "exec",
                f"redpanda_{listener_port}",
                "rpk",
                "topic",
                "create",
                topic,
                pattern=topic,
                timeout=10,
            )
            for topic in self.topics
        ]

    try:
        return_values = [
            await asyncio.wait_for(process.value.wait(), 30) for process in processes
        ]
        if any(return_value != 0 for return_value in return_values):
            raise ValueError("Could not create missing topics!")
    except asyncio.TimeoutError as _:
        raise ValueError("Timed out while creating missing topics!")


@patch
async def _start(self: LocalRedpandaBroker) -> str:
    await self._check_deps()

    self.temporary_directory = TemporaryDirectory()
    self.temporary_directory_path = Path(self.temporary_directory.__enter__())

    await self._start_redpanda()
    await asyncio.sleep(5)

    listener_port = self.redpanda_kwargs.get("listener_port", 9092)
    bootstrap_server = f"127.0.0.1:{listener_port}"
    logger.info(f"Local Redpanda broker up and running on {bootstrap_server}")

    await self._create_topics()

    self._is_started = True

    return bootstrap_server


@patch
async def _stop(self: LocalRedpandaBroker) -> None:
    logger.info(f"Stopping redpanda...")
    await terminate_asyncio_process(self.redpanda_task)  # type: ignore
    logger.info(f"Redpanda stopped.")
    self.temporary_directory.__exit__(None, None, None)  # type: ignore
    self._is_started = False

# %% ../../nbs/003_LocalRedpandaBroker.ipynb 17
@patch
def start(self: LocalRedpandaBroker) -> str:
    """Starts a local redpanda broker instance synchronously
    Returns:
       Redpanda broker bootstrap server address in string format: add:port
    """
    logger.info(f"{self.__class__.__name__}.start(): entering...")
    try:
        # get or create loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError as e:
            logger.warning(
                f"{self.__class__.__name__}.start(): RuntimeError raised when calling asyncio.get_event_loop(): {e}"
            )
            logger.warning(
                f"{self.__class__.__name__}.start(): asyncio.new_event_loop()"
            )
            loop = asyncio.new_event_loop()

        # start redpanda broker in the loop

        if loop.is_running():
            if self.apply_nest_asyncio:
                logger.warning(
                    f"{self.__class__.__name__}.start(): ({loop}) is already running!"
                )
                logger.warning(
                    f"{self.__class__.__name__}.start(): calling nest_asyncio.apply()"
                )
                nest_asyncio.apply(loop)
            else:
                msg = f"{self.__class__.__name__}.start(): ({loop}) is already running! Use 'apply_nest_asyncio=True' when creating 'LocalRedpandaBroker' to prevent this."
                logger.error(msg)
                raise RuntimeError(msg)

        retval = loop.run_until_complete(self._start())
        logger.info(f"{self.__class__}.start(): returning {retval}")
        return retval
    finally:
        logger.info(f"{self.__class__.__name__}.start(): exited.")


@patch
def stop(self: LocalRedpandaBroker) -> None:
    """Stops a local redpanda broker instance synchronously
    Returns:
       None
    """
    logger.info(f"{self.__class__.__name__}.stop(): entering...")
    try:
        if not self._is_started:
            raise RuntimeError(
                "LocalRedpandaBroker not started yet, please call LocalRedpandaBroker.start() before!"
            )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._stop())
    finally:
        logger.info(f"{self.__class__.__name__}.stop(): exited.")
