# Image And File Workflows

Use this reference when a request mentions an uploaded image, document, file,
rendering, screenshot, native image generation, or visual transformation.

## Core Rule

AirPrompter workflows provide instructions. The host agent handles host-local
files and host-native tools unless AirPrompter explicitly has an upload/write
tool for that artifact.

If the user says to use AirPrompter on an image or file:

1. Use AirPrompter MCP to find and run the saved workflow.
2. Treat the uploaded image or file as host-local context.
3. Pass only supported textual metadata or references into AirPrompter tools.
4. Execute returned prompt instructions against the host-local image or file.
5. If AirPrompter returns an image-generation prompt, use the host's native
   image-generation tool with that prompt when available.
6. If the host has no image-generation tool, return the generated prompt and
   clearly say rendering was not available in this host.

Do not claim the image was uploaded to AirPrompter unless an AirPrompter write
tool actually uploaded it.

Do not read files, search the web, generate images, or edit images with native
tools before AirPrompter starts or returns a failure. Native tools are the
handoff target after AirPrompter returns `promptText`, not a substitute for the
saved workflow.

## No Substitute Results

If AirPrompter cannot find or run the requested workflow, stop and explain the
AirPrompter failure. Do not generate an image or file result directly as a
replacement.
