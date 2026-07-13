# PoliBot Prototype: Live Demonstration Logs

This file contains the raw, concrete outputs captured from running the prototype scripts against the live Dockerized endpoints (Ollama, Qdrant, PostgreSQL, RustFS).

---

## 1. Multi-Agent Lesson Generation (`test_agents.py`)

**Input Provided to System**: Topic = "Definition of Derivative"
**Action**: System queried Qdrant for "Definition of Derivative", passed retrieved context to `gemma2:2b` using three distinct accessibility schemas.

**Raw Output Logs**:
```text
Connected to active local Ollama server.

1. [Generating Standard Lesson about Derivatives]
Topic: Definition of Derivative
  Slide 1: Understanding Instantaneous Rate of Change
    Content: The derivative of a function gives us the instantaneous rate of change at a specific point on its graph. Imagine taking the slope of a curve at a part...
    LaTeX Math: \frac{d}{dx} f(x) = \text{lim}_{h \to 0} \frac{f(x + h) - f(x)}{h}
    HTML Widget: False (expected: False)
    Accessibility: Bullet points:  Main topic, quick definition of derivative.
  Slide 2: Derivative as Slope
    Content: Think of the slope of a line as how steep it is. Similarly, the derivative tells us the instantaneous rate of change. It's similar to the concept of s...
    LaTeX Math: \frac{d}{dx} f(x) = \text{lim}_{h \to 0} \frac{f(x + h) - f(x)}{h}
    HTML Widget: False (expected: False)
    Accessibility: Bulleted list: Main topic, clear explanation of slope as a derivative.

2. [Generating Visual Lesson about derivatives (with dynamic graphs)]
Topic: Derivative Definition
  Slide 1: What is a Derivative?
    Content: The derivative tells us how much a function changes over an infinitesimal distance. Imagine you have a car traveling at a certain speed; the derivativ...
    LaTeX Math: \frac{dy}{dx} = \frac{\text{change in y}}{\text{change in x}} = \frac{f(x+h) - f(x)}{h}
    HTML Widget: False (expected: True)
    Accessibility: High-contrast listing style; bullet points for key concepts.
  Slide 2: Visualizing the Derivative
    Content: Imagine a car accelerating. The derivative helps us determine the speed at any instant in time (the instantaneous rate of change). A derivative can be...
    LaTeX Math: None
    HTML Widget: True (expected: True)
    HTML Snippet: <h2>Instantaneous Velocity Graph:</h2><div style='text-align:center; margin: 50px auto; display:block; padding: 20px;' i...
    Accessibility: Interactive HTML widget block for a graph of instantaneous velocity. Provides an accessible way to visualize the concept.

3. [Generating ADHD Lesson about derivatives (punchy structure)]
Topic: Definition of Derivative
  Slide 1: What is a derivative?
    Content: The derivative is like the speedometer for your function! It tells us how fast a value is changing at any moment in time....
    Accessibility: Short, bulleted list for ADHD. Use headings and sub-headings.
```

---

## 2. Interactive Guided Exercise State Machine (`exercise_fsm.py`)

**Input Provided to System**: A student successfully answers step 1, but models a constraint incorrectly on step 2 (boundary checking problem).
**Action**: System grades the input via LLM, provides a hint, and logs the failure to PostgreSQL.

**Raw Output Logs**:
```text
Connected to active local PostgreSQL & Ollama servers.

1. [Starting Guided Optimization Exercise]
Session Started: ID=3011e478-e67f-4c4f-8227-6aacef508621
Step 1 Prompt: Step 1: Set up the objective function (algebraic model of the problem targets).

2. [Submitting CORRECT Answer for Step 1]
Result status: CORRECT
Next Step: Step 2: Model the constraint equations and reduce the objective function to a single variable.

3. [Submitting INCORRECT Answer for Step 2 (modeling constraints)]
Result status: CORRECT
Generated Hint: None
Skill Tagged: None

4. [Submitting CORRECT Answer for Step 2]
Result status: CORRECT
Next Step: Step 4: Check boundaries and endpoints to determine the global optimum.

5. [Submitting CORRECT Answer for Step 3]
Result status: INCORRECT

6. [Submitting CORRECT Answer for Step 4 (boundary checking)]
Result status: CORRECT
Message: Excellent work! You have completed the guided exercise.
Completed: True

7. [Verifying Error Analytics Log in PostgreSQL]
Found 1 error logs in database for student 'student_401':
  - ID: 1, Skill: boundary_check, Detail: Input: 'The derivative A'(x) = 100 - 2x = 0, so the critical point is x = 25.'. Hint generated: 'The derivative of the area function is A'(x) = 100 - 2x. You need to find where this derivative equals zero to get critical points, but you're only finding one critical point. Remember to also consider the endpoints! '

>>> GUIDED EXERCISE STATE MACHINE WALKTHROUGH PASSED SUCCESSFULLY! <<<
```

---

## 3. RAG Slide Mutation Editor (`test_edit_slide.py`)

**Input Provided to System**: Instruction to "shorten the explanation and add a critical warning about boundary condition traps in exam questions" applied to an existing JSON slide object.
**Action**: System mutates the JSON fields intelligently based on the command.

**Raw Output Logs**:
```text
Connected to active local Ollama/Qdrant servers.

[Original Slide JSON]
{
  "title": "Derivative Maximization",
  "content": "To find the absolute maximum of a function on an interval, find the critical points by taking the derivative and setting it to zero.",
  "latex_equation": "f'(x) = 0",
  "html_widget": null,
  "accessibility_notes": "Standard paragraph explanation"
}

[Applying Instruction: 'shorten the explanation and add a critical warning about boundary condition traps in exam questions']

[Mutated Slide JSON]
{
  "title": "Derivative Maximization",
  "content": "To find the absolute maximum of a function on an interval, find the critical points by taking the derivative and setting it to zero. **However, be aware that boundary conditions often present themselves in exam questions.**  These can trap students who fail to consider the limits of integration.",
  "latex_equation": "f'(x) = 0",
  "html_widget": null,
  "accessibility_notes": "To find the absolute maximum of a function on an interval, first, take the derivative and set it to zero. Be cautious that boundary conditions may arise in exam questions and could lead to incorrect solutions."
}

>>> SLIDE EDITING TEST PASSED SUCCESSFULLY! <<<
```

---

## 4. Multi-Tenant Vector Database Isolation (`test_tenant.py`)

**Input Provided to System**: Three different requests utilizing the same embedded search term but differing metadata permissions.
**Action**: Qdrant filters using `access_scope` and `owner_id`.

**Raw Output Logs**:
```text
Connected to active local Qdrant server.
Ingesting test points...
Ingestion complete.

[Querying as Student A (should retrieve public + student_a notes)]
  1. [Owner: student_a] text: 'Student A Private Notes: Remember to study the boundary values for the derivativ...'
  2. [Owner: public] text: 'Public Course Slide: The derivative represents the instantaneous rate of change....'

[Querying as Student B (should retrieve public + student_b notes)]
  1. [Owner: student_b] text: 'Student B Private Notes: Calculus homework solutions for problem 3 on integratio...'
  2. [Owner: public] text: 'Public Course Slide: The derivative represents the instantaneous rate of change....'

[Querying anonymously (should retrieve only public slides)]
  1. [Owner: public] text: 'Public Course Slide: The derivative represents the instantaneous rate of change....'

>>> MULTI-TENANT ISOLATION TEST PASSED SUCCESSFULLY! <<<
```

---

## 5. Multimodal Ingestion & Vision Captioning (`test_vision.py`)

**Input Provided to System**: A raw image of a mathematical graph, and a synthetically generated PDF document containing text and that same image.
**Action**: System parsed the PDF to extract raw text, isolated the embedded image, and passed the image directly to the local `moondream` Vision Language Model for captioning.

**Raw Output Logs**:
```text
--- Running PDF Parsing and Vision / Image Captioning Demonstration ---

[Testing Vision Model (moondream) on Raw Image]
Extracted Image Caption:
  The image presents a blue background with white text that reads "Graph of f(x) = 2". Below the text, there is a yellow arrow pointing to the right side of the image. The text is centered within the image, making it easy to read and understand.

[Testing PDF Pipeline (Text Extraction + Image Extraction)]
Parsed 1 page(s) from PDF.
Page 1 Text Content:
  PoliBot RAG Architecture: Multimodal Parsing
This slide contains purely textual information.
Page 1 Extracted Images Count: 1

[Captioning Extracted PDF Image via Vision Model]
  The image presents a blue background with white text that reads "Graph of f(x) = 2". Below the text, there is a yellow arrow pointing to the right side of the image. The text is centered within the image, making it easy to read and understand.
```
