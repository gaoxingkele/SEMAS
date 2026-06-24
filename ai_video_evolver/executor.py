"""Executor for the AI Video Evolver pipeline.

The executor receives the pipeline agent (whose `topology` points to the video
workflow), runs each node agent sequentially, and returns the final state
containing `final_prompt` and `clip`.
"""

from __future__ import annotations

from typing import Any

from semas.genome.genome import AgentGenome
from semas.genome.repository import GenomeRepository


def _exec_tool(repo: GenomeRepository, tool_name: str) -> dict[str, Any]:
    """Execute a tool source file in a fresh namespace and return it."""
    tool = repo.load_tool(tool_name)
    namespace: dict[str, Any] = {}
    exec(tool.source_code, namespace)  # noqa: S102
    return namespace


def _execute_node(
    node_agent: AgentGenome,
    state: dict[str, Any],
    repo: GenomeRepository,
) -> dict[str, Any]:
    """Execute a single node in the video pipeline."""
    name = node_agent.name
    prompt_lower = node_agent.system_prompt.lower()

    if name == "scriptwriter":
        user_idea = state.get("user_idea", "")
        state["scene_description"] = f"A scene showing {user_idea}."
        return state

    if name == "prompt_engineer":
        scene = state.get("scene_description", "")
        # The pipeline agent (passed to the executor) carries the meta flag.
        pipeline_meta = state.get("_pipeline_meta", {})
        use_enhancement = pipeline_meta.get("prompt_engineering", {}).get(
            "use_enhancement", False
        )
        if use_enhancement or "prompt_templates" in node_agent.tools or "enhance" in prompt_lower:
            ns = _exec_tool(repo, "prompt_templates")
            enhancer = ns.get("enhance_prompt")
            if callable(enhancer):
                state["final_prompt"] = enhancer(scene, style="cinematic")
            else:
                state["final_prompt"] = scene
        else:
            state["final_prompt"] = scene
        return state

    if name == "asset_generator":
        final_prompt = state.get("final_prompt", "")
        ns = _exec_tool(repo, "video_api_client")
        generator = ns.get("generate_video_from_prompt")
        if callable(generator):
            state["clip"] = generator(final_prompt)
        else:
            state["clip"] = {"error": "no generator"}
        return state

    if name == "editor":
        clip = state.get("clip", {})
        captions = state.get("captions", "")
        ns = _exec_tool(repo, "ffmpeg_pipeline")
        editor_fn = ns.get("add_captions_and_normalize")
        if callable(editor_fn):
            state["clip"] = editor_fn(clip, captions)
        return state

    if name == "critic":
        # The actual scoring is done by the evaluator; here we just pass through.
        return state

    return state


def create_video_executor(repo: GenomeRepository):
    """Return an ExecutorFn that runs the video pipeline topology."""

    def executor(agent: AgentGenome, task_input: dict[str, Any]) -> dict[str, Any]:
        if agent.topology is None:
            raise ValueError("Pipeline agent must have a topology defined")

        topology = repo.load_topology(agent.topology)
        state = dict(task_input)
        state["_pipeline_meta"] = agent.meta
        for node_name in topology.nodes:
            node_agent = repo.load_agent(node_name)
            state = _execute_node(node_agent, state, repo)

        return state

    return executor
