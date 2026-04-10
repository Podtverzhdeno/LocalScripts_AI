"""Pydantic schemas for LocalScript project structures."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """Information about a file in the project."""
    name: str = Field(..., description="Filename (e.g., 'config.lua')")
    purpose: str = Field(..., description="What this file does")
    dependencies: List[str] = Field(default_factory=list, description="List of files this depends on")


class ProjectPlan(BaseModel):
    """Project architecture plan from Architect agent."""
    files: List[FileInfo] = Field(..., description="List of files in the project")
    structure: str = Field(..., description="Brief architecture description")
    order: List[str] = Field(..., description="Build order (dependencies first)")


class FunctionSpec(BaseModel):
    """Specification for a single function."""
    name: str = Field(..., description="Function name")
    params: List[str] = Field(default_factory=list, description="Parameter names")
    returns: str = Field(..., description="Return type description")
    description: str = Field(..., description="What this function does")


class DataStructure(BaseModel):
    """Data structure specification."""
    name: str = Field(..., description="Structure name")
    fields: List[str] = Field(default_factory=list, description="Field names")


class FileSpecification(BaseModel):
    """Detailed specification for a single file."""
    file: str = Field(..., description="Filename")
    functions: List[FunctionSpec] = Field(default_factory=list, description="Functions to implement")
    dependencies_api: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Available APIs from dependencies"
    )
    data_structures: List[DataStructure] = Field(
        default_factory=list,
        description="Data structures used"
    )
    edge_cases: List[str] = Field(default_factory=list, description="Edge cases to handle")
    example_usage: str = Field(default="", description="Example usage code")


class IntegrationIssue(BaseModel):
    """Issue found during integration testing."""
    file: str = Field(..., description="File with the issue")
    problem: str = Field(..., description="Description of the problem")
    fix: str = Field(..., description="Suggested fix")


class ImprovementSuggestion(BaseModel):
    """Code improvement suggestion."""
    file: str = Field(..., description="File to improve")
    issue: str = Field(..., description="Issue description")
    suggestion: str = Field(..., description="Improvement suggestion")


class EvolutionAnalysis(BaseModel):
    """Analysis from Evolver agent."""
    improvements: List[ImprovementSuggestion] = Field(
        default_factory=list,
        description="List of improvements"
    )
    priority: str = Field(default="low", description="Priority: high, medium, low")
    should_evolve: bool = Field(default=False, description="Whether evolution is needed")
