# ========== core/v8/planning_remote.py ==========
# Phase 35 — Remote Multi-Step Task Planning DAG

from typing import List, Dict
from core.intelligence.types import PlanStep, AgentPlan, PlanStatus
from core.intelligence.planner import DependencyGraph


def create_remote_wake_and_verify_dag(device_id: str, mac_address: str) -> AgentPlan:
    """
    Masofadan kompyuterni uyg'otish va holatini tekshirish DAG rejasi:
    CHECK_DEVICE -> WAKE_DEVICE -> WAIT_HEARTBEAT -> VERIFY_ONLINE -> GET_STATUS
    """
    s1 = PlanStep(
        step_id="check_device",
        order=1,
        intent="remote_check",
        description="Qurilma holatini tekshirish",
        tool="status",
        parameters={"device_id": device_id},
        dependencies=[]
    )
    s2 = PlanStep(
        step_id="wake_device",
        order=2,
        intent="wol_wake",
        description="Wake-on-LAN paketi jo'natish",
        tool="wake",
        parameters={"device_id": device_id, "mac_address": mac_address},
        dependencies=["check_device"]
    )
    s3 = PlanStep(
        step_id="wait_heartbeat",
        order=3,
        intent="wait_heartbeat",
        description="Agent heartbeat javobini kutish",
        tool="wait_heartbeat",
        parameters={"device_id": device_id, "timeout": 45},
        dependencies=["wake_device"]
    )
    s4 = PlanStep(
        step_id="verify_online",
        order=4,
        intent="verify_online",
        description="Qurilma online ekanligini tasdiqlash",
        tool="verify_online",
        parameters={"device_id": device_id},
        dependencies=["wait_heartbeat"]
    )
    s5 = PlanStep(
        step_id="get_status",
        order=5,
        intent="system_info",
        description="Tizim holati va resurslarini olish",
        tool="system_info",
        parameters={"device_id": device_id},
        dependencies=["verify_online"]
    )

    steps = [s1, s2, s3, s4, s5]
    graph = DependencyGraph.build_graph(steps)
    order = DependencyGraph.compute_execution_order(steps, graph)

    return AgentPlan(
        plan_id=f"remote_wake_{device_id}",
        goal=f"Kompyuterni ({device_id}) uyg'otish va holatini olish",
        intent="remote_wake_and_status",
        steps=steps,
        dependencies=graph,
        execution_order=order,
        status=PlanStatus.PENDING
    )
