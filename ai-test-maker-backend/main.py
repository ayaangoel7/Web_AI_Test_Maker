import customtkinter as ctk  # type: ignore
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import json
import os
from pathlib import Path
from datetime import datetime
import time

# Import our modules
from pdf_processor import PDFProcessor
from ai_engine import AIEngine
from test_generator import TestGenerator
from test_grader import TestGrader
from question_customizer import QuestionCustomizer


class AITestMaker(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("AI Test Maker")
        self.geometry("1200x800")

        # Theme colors
        self.bg_color = "#1E1E2E"
        self.panel_color = "#2A2A3C"
        self.button_color = "#4A90E2"
        self.correct_color = "#2ECC71"
        self.wrong_color = "#E74C3C"

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=self.bg_color)

        # Initialize components
        self.pdf_processor = PDFProcessor()
        self.ai_engine = AIEngine()
        self.test_generator = TestGenerator(self.ai_engine)
        self.test_grader = TestGrader(self.ai_engine)
        self.question_customizer = QuestionCustomizer()

        # State variables
        self.file_path = None
        self.selected_marks = tk.IntVar(value=10)
        self.test_data = None
        self.user_answers = {}
        self.results = None
        self.pdf_content = None
        self.custom_distribution = None
        self.spinbox_refs = {}
        self.current_distribution = {}
        self.is_retake = False

        # Show upload screen first
        self.show_upload_screen()

        # Check models after window is ready
        self.after(100, self.check_and_download_models)

    def ensure_models_loaded(self):
        """Ensure models are loaded before generation"""
        try:
            if self.ai_engine.llm is None:
                print("DEBUG: Models not loaded, reloading...")
                self.ai_engine.load_models()
                print("DEBUG: Models reloaded successfully.")
            else:
                print("DEBUG: Models already loaded.")
        except Exception as e:
            print(f"DEBUG: Model load error: {e}")
            messagebox.showerror("Model Error", f"Failed to load models: {str(e)}\nTry restarting the app.")
            return False
        return True

    def check_and_download_models(self):
        """Check if models exist, download if needed"""
        if not self.ai_engine.models_exist():
            print("DEBUG: Models not found, starting download...")
            self.show_model_download_screen()
        else:
            print("DEBUG: Models exist, ensuring loaded...")
            self.ensure_models_loaded()

    def show_model_download_screen(self):
        """Show model download screen"""
        self.clear_screen()

        # Check if window already exists to avoid double-open error
        if hasattr(self, "loading_window") and self.loading_window.winfo_exists():
            try:
                self.loading_window.lift()
            except Exception:
                pass
            return

        self.loading_window = ctk.CTkToplevel(self)
        self.loading_window.title("First Run Setup")
        self.loading_window.geometry("500x200")
        self.loading_window.configure(fg_color=self.bg_color)
        self.loading_window.transient(self)

        try:
            self.loading_window.grab_set()
        except Exception:
            # If grab fails, continue without it
            pass

        self.loading_label = ctk.CTkLabel(
            self.loading_window,
            text="Downloading AI models for first run...\nThis may take several minutes.",
            font=("Helvetica", 16),
            text_color="white"
        )
        self.loading_label.pack(pady=20)

        self.loading_progress = ctk.CTkProgressBar(self.loading_window, width=400)
        self.loading_progress.pack(pady=10)
        self.loading_progress.set(0)

        self.loading_status = ctk.CTkLabel(
            self.loading_window,
            text="Starting download...",
            font=("Helvetica", 12),
            text_color="#AAAAAA"
        )
        self.loading_status.pack(pady=(0, 20))

        self.download_thread = threading.Thread(
            target=self.ai_engine.download_models_safe,
            args=(self.update_download_progress,),
            daemon=True
        )
        self.download_thread.start()

    def update_download_progress(self, progress, status=""):
        """Update progress from download thread"""
        if progress is not None:
            self.loading_progress.set(progress)
        if status:
            self.loading_status.configure(text=status)
        if progress >= 1.0:
            self.loading_label.configure(text="Models downloaded! Loading...")
            self.after(1000, self.download_complete)

    def download_complete(self):
        """Handle download completion"""
        if hasattr(self, 'loading_window') and self.loading_window.winfo_exists():
            self.loading_window.destroy()
            del self.loading_window

        # Ensure models loaded after download
        self.ensure_models_loaded()
        self.show_upload_screen()
        messagebox.showinfo("Setup Complete", "Models are ready! You can now generate tests.")

    def clear_screen(self):
        """Clear all widgets from window"""
        try:
            for widget in self.winfo_children():
                widget.destroy()
        except tk.TclError:
            pass

    def show_upload_screen(self):
        """Screen 1: Upload File & Select Marks"""
        self.clear_screen()

        self.file_path = None
        self.pdf_content = None
        self.custom_distribution = None

        container = ctk.CTkFrame(self, fg_color=self.panel_color, corner_radius=15)
        container.pack(expand=True, fill="both", padx=40, pady=40)

        title = ctk.CTkLabel(
            container,
            text="AI Test Maker",
            font=("Helvetica", 28, "bold"),
            text_color="white"
        )
        title.pack(pady=(40, 20))

        subtitle = ctk.CTkLabel(
            container,
            text="Upload a PDF or Word document and generate a custom test",
            font=("Helvetica", 16),
            text_color="#AAAAAA"
        )
        subtitle.pack(pady=(0, 40))

        pdf_frame = ctk.CTkFrame(container, fg_color=self.bg_color, corner_radius=10)
        pdf_frame.pack(pady=20, padx=60, fill="x")

        self.file_label = ctk.CTkLabel(
            pdf_frame,
            text="No file selected",
            font=("Helvetica", 14),
            text_color="#AAAAAA"
        )
        self.file_label.pack(pady=20, padx=20)

        upload_btn = ctk.CTkButton(
            pdf_frame,
            text="Upload File",
            font=("Helvetica", 14, "bold"),
            fg_color=self.button_color,
            hover_color="#357ABD",
            height=40,
            width=200,
            command=self.upload_file
        )
        upload_btn.pack(pady=(0, 20))

        marks_label = ctk.CTkLabel(
            container,
            text="Select Test Marks:",
            font=("Helvetica", 18, "bold"),
            text_color="white"
        )
        marks_label.pack(pady=(30, 20))

        marks_frame = ctk.CTkFrame(container, fg_color="transparent")
        marks_frame.pack(pady=10)

        marks_options = [10, 25, 50, 100]
        for marks in marks_options:
            rb = ctk.CTkRadioButton(
                marks_frame,
                text=f"{marks} Marks",
                variable=self.selected_marks,
                value=marks,
                font=("Helvetica", 16),
                text_color="white",
                fg_color=self.button_color,
                hover_color="#357ABD"
            )
            rb.pack(side="left", padx=15)

        generate_btn = ctk.CTkButton(
            container,
            text="Next: Customize Questions",
            font=("Helvetica", 16, "bold"),
            fg_color=self.button_color,
            hover_color="#357ABD",
            height=50,
            width=250,
            command=self.show_distribution_screen
        )
        generate_btn.pack(pady=40)

    def upload_file(self):
        """Handle PDF or DOCX upload"""
        filepath = filedialog.askopenfilename(
            title="Select PDF or Word File",
            filetypes=[
                ("Supported Files", "*.pdf *.docx"),
                ("PDF Files", "*.pdf"),
                ("Word Documents", "*.docx")
            ]
        )

        if filepath:
            self.file_path = filepath
            filename = os.path.basename(filepath)
            self.file_label.configure(text=f"Selected: {filename}", text_color="white")

    def show_distribution_screen(self):
        """Screen 1.5: Customize question distribution"""
        if not self.file_path:
            messagebox.showerror("Error", "Please upload a file first!")
            return

        self.clear_screen()

        marks = self.selected_marks.get()

        # Get default distribution
        default_dist = self.question_customizer.get_default_distribution(marks)

        container = ctk.CTkFrame(self, fg_color=self.panel_color, corner_radius=15)
        container.pack(expand=True, fill="both", padx=40, pady=40)

        title = ctk.CTkLabel(
            container,
            text="Customize Question Distribution",
            font=("Helvetica", 28, "bold"),
            text_color="white"
        )
        title.pack(pady=(30, 10))

        subtitle = ctk.CTkLabel(
            container,
            text=f"Total Marks: {marks} | Adjust the number of each question type",
            font=("Helvetica", 14),
            text_color="#AAAAAA"
        )
        subtitle.pack(pady=(0, 30))

        # Create scrollable frame for question types
        scroll_frame = ctk.CTkScrollableFrame(
            container,
            fg_color=self.bg_color,
            corner_radius=10
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Store spinbox references for later
        self.spinbox_refs = {}
        self.current_distribution = default_dist.copy()

        q_types = self.question_customizer.get_question_types()

        for q_type in q_types:
            q_frame = ctk.CTkFrame(scroll_frame, fg_color=self.panel_color, corner_radius=10)
            q_frame.pack(fill="x", pady=10, padx=5)

            # Question type label with marks per question
            marks_per = self.question_customizer.marks_per_type[q_type]
            left_label = ctk.CTkLabel(
                q_frame,
                text=f"{q_type} ({marks_per} mark{'s' if marks_per > 1 else ''})",
                font=("Helvetica", 14, "bold"),
                text_color="white",
                anchor="w"
            )
            left_label.pack(side="left", padx=15, pady=15)

            # Numeric control for count: [-]  [entry]  [+]
            count_var = tk.IntVar(value=default_dist.get(q_type, 0))

            def make_dec_callback(q_t, var):
                def _dec():
                    val = var.get() - 1
                    if val < 0:
                        val = 0
                    var.set(val)
                    # Update entry display
                    self.spinbox_refs[q_t]["entry"].delete(0, tk.END)
                    self.spinbox_refs[q_t]["entry"].insert(0, str(val))
                    self.on_count_changed(q_t, var, marks)
                return _dec

            def make_inc_callback(q_t, var):
                def _inc():
                    val = var.get() + 1
                    if val > 100:
                        val = 100
                    var.set(val)
                    # Update entry display
                    self.spinbox_refs[q_t]["entry"].delete(0, tk.END)
                    self.spinbox_refs[q_t]["entry"].insert(0, str(val))
                    self.on_count_changed(q_t, var, marks)
                return _inc

            dec_btn = ctk.CTkButton(
                q_frame,
                text="-",
                width=30,
                height=28,
                command=make_dec_callback(q_type, count_var),
                fg_color=self.button_color,
                hover_color="#357ABD",
            )
            dec_btn.pack(side="left", padx=(20, 5), pady=15)

            entry = ctk.CTkEntry(
                q_frame,
                width=50,
                font=("Helvetica", 14),
                justify="center",
            )
            entry.insert(0, str(count_var.get()))
            entry.pack(side="left", padx=5, pady=15)

            inc_btn = ctk.CTkButton(
                q_frame,
                text="+",
                width=30,
                height=28,
                command=make_inc_callback(q_type, count_var),
                fg_color=self.button_color,
                hover_color="#357ABD",
            )
            inc_btn.pack(side="left", padx=5, pady=15)

            # Marks earned label
            marks_label = ctk.CTkLabel(
                q_frame,
                text=f"0 marks",
                font=("Helvetica", 12),
                text_color="#4A90E2"
            )
            marks_label.pack(side="right", padx=15, pady=15)

            # Keep entry and IntVar in sync
            def make_entry_callback(q_t, var, ent):
                def _on_entry_change(*args):
                    try:
                        val = int(ent.get())
                    except ValueError:
                        val = 0
                    if val < 0:
                        val = 0
                    if val > 100:
                        val = 100
                    var.set(val)
                    self.on_count_changed(q_t, var, marks)
                return _on_entry_change

            entry.bind("<KeyRelease>", make_entry_callback(q_type, count_var, entry))

            # Store references
            self.spinbox_refs[q_type] = {
                "var": count_var,
                "entry": entry,
                "marks_label": marks_label,
            }

        # Total marks display frame
        total_frame = ctk.CTkFrame(container, fg_color=self.bg_color, corner_radius=10)
        total_frame.pack(fill="x", padx=20, pady=20)

        self.total_display = ctk.CTkLabel(
            total_frame,
            text=f"Total: 0 / {marks} marks",
            font=("Helvetica", 18, "bold"),
            text_color="#4A90E2"
        )
        self.total_display.pack(pady=15)

        # Error message display
        self.error_display = ctk.CTkLabel(
            total_frame,
            text="",
            font=("Helvetica", 12),
            text_color=self.wrong_color
        )
        self.error_display.pack(pady=5)

        # Button frame
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(pady=20)

        back_btn = ctk.CTkButton(
            button_frame,
            text="Back",
            font=("Helvetica", 14, "bold"),
            fg_color="#555555",
            hover_color="#666666",
            height=40,
            width=150,
            command=self.show_upload_screen
        )
        back_btn.pack(side="left", padx=10)

        self.generate_btn = ctk.CTkButton(
            button_frame,
            text="Generate Test",
            font=("Helvetica", 14, "bold"),
            fg_color=self.button_color,
            hover_color="#357ABD",
            height=40,
            width=150,
            command=self.generate_test
        )
        self.generate_btn.pack(side="left", padx=10)

        # Update displays initially (AFTER button is created)
        self.on_count_changed(None, None, marks)

    def on_count_changed(self, q_type, count_var, total_marks):
        """Handle change in question count"""
        # Update current distribution from all controls
        for q_t, refs in self.spinbox_refs.items():
            self.current_distribution[q_t] = refs["var"].get()

        # Calculate total marks
        total = self.question_customizer.calculate_total_marks(self.current_distribution)

        # Update marks display for each type
        for q_t, refs in self.spinbox_refs.items():
            count = refs["var"].get()
            marks_per = self.question_customizer.marks_per_type[q_t]
            earned = count * marks_per
            refs["marks_label"].configure(text=f"{earned} marks")

        # Update total display and enable/disable generate button
        if hasattr(self, 'generate_btn'):
            if total == total_marks:
                self.total_display.configure(
                    text=f"Total: {total} / {total_marks} marks ✓",
                    text_color=self.correct_color
                )
                self.error_display.configure(text="")
                self.generate_btn.configure(state="normal")
            elif total < total_marks:
                self.total_display.configure(
                    text=f"Total: {total} / {total_marks} marks",
                    text_color="#FFA500"
                )
                self.error_display.configure(
                    text=f"Need {total_marks - total} more marks",
                    text_color="#FFA500"
                )
                self.generate_btn.configure(state="disabled")
            else:
                self.total_display.configure(
                    text=f"Total: {total} / {total_marks} marks",
                    text_color=self.wrong_color
                )
                self.error_display.configure(
                    text=f"Exceeds by {total - total_marks} marks",
                    text_color=self.wrong_color
                )
                self.generate_btn.configure(state="disabled")

    def generate_test(self):
        """Generate test from the uploaded file"""
        if not self.file_path:
            messagebox.showerror("Error", "Please upload a file first!")
            return

        marks = self.selected_marks.get()

        # Ensure models loaded before starting
        if not self.ensure_models_loaded():
            return

        # Use custom distribution if set, else use defaults
        custom_dist = self.current_distribution if self.current_distribution else \
                      self.question_customizer.get_default_distribution(marks)

        self.clear_screen()

        loading_label = ctk.CTkLabel(
            self,
            text="Please wait while test is being generated...\n\nThis may take 30-60 seconds depending on test size.",
            font=("Helvetica", 18),
            text_color="white"
        )
        loading_label.pack(expand=True)

        self.test_progress = ctk.CTkProgressBar(self, width=400)
        self.test_progress.pack(pady=20)
        self.test_progress.set(0)

        def generation_thread():
            try:
                print("DEBUG: Starting generation thread...")
                self.after(0, lambda: self.test_progress.set(0.1))
                time.sleep(0.1)

                # For retake or new file, clear cache if new file
                if self.pdf_content is None or (hasattr(self, 'is_retake') and self.is_retake):
                    print("DEBUG: Processing file...")
                    self.pdf_content = self.pdf_processor.process_file(self.file_path, marks)
                    self.is_retake = False

                print("DEBUG: Generating test with LLM...")
                self.after(0, lambda: self.test_progress.set(0.5))
                time.sleep(0.1)

                # Pass custom distribution to test generator
                self.test_data = self.test_generator.generate_test_custom(
                    self.pdf_content,
                    marks,
                    custom_dist
                )

                # Sort the questions by type
                if self.test_data and self.test_data['questions']:
                    print("DEBUG: Sorting questions...")
                    q_type_order = {
                        'MCQ': 0,
                        'Very Short': 1,
                        'Short(I)': 2,
                        'Short(II)': 3,
                        'Long Answer': 4
                    }
                    self.test_data['questions'].sort(
                        key=lambda q: q_type_order.get(q['type'], 99)
                    )
                    print("DEBUG: Questions sorted.")


                print("DEBUG: Test generated successfully!")
                self.after(0, lambda: self.test_progress.set(1.0))
                time.sleep(0.5)

                self.after(0, self.show_test_screen)

            except Exception as e:
                print(f"DEBUG: Generation error: {e}")
                self.after(0, lambda: messagebox.showerror("Generation Error", f"Failed to generate test: {str(e)}\nCheck console for details."))
                self.after(0, self.show_upload_screen)

        thread = threading.Thread(target=generation_thread, daemon=True)
        thread.start()

    def show_test_screen(self):
        """Screen 2: Take Test"""
        if not self.test_data:
            return

        self.clear_screen()

        header = ctk.CTkFrame(self, fg_color=self.panel_color, height=100)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="Take Your Test",
            font=("Helvetica", 22, "bold"),
            text_color="white"
        )
        title.pack(pady=(15, 5))

        info = ctk.CTkLabel(
            header,
            text=f"Total Marks: {self.test_data['total_marks']} | Questions: {len(self.test_data['questions'])}",
            font=("Helvetica", 14),
            text_color="#AAAAAA"
        )
        info.pack()

        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=self.bg_color,
            corner_radius=10
        )
        scroll_frame.pack(expand=True, fill="both", padx=20, pady=10)

        self.user_answers = {}

        for i, question in enumerate(self.test_data['questions'], 1):
            self.create_question_widget(scroll_frame, question, i)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        submit_btn = ctk.CTkButton(
            button_frame,
            text="Submit Test",
            font=("Helvetica", 14, "bold"),
            fg_color=self.button_color,
            hover_color="#357ABD",
            height=45,
            width=200,
            command=self.submit_test
        )
        submit_btn.pack(side="left", padx=5)

    def create_question_widget(self, parent, question, num):
        """Create widget for a single question"""
        q_frame = ctk.CTkFrame(parent, fg_color=self.panel_color, corner_radius=10)
        q_frame.pack(fill="x", pady=10, padx=10)

        header_text = f"Q{num}. [{question['marks']} mark{'s' if question['marks'] > 1 else ''}] - {question['type']}"
        header = ctk.CTkLabel(
            q_frame,
            text=header_text,
            font=("Helvetica", 14, "bold"),
            text_color="#4A90E2",
            anchor="w"
        )
        header.pack(fill="x", padx=15, pady=(15, 5))

        q_text = ctk.CTkLabel(
            q_frame,
            text=question["question"],
            font=("Helvetica", 16),
            text_color="white",
            anchor="w",
            wraplength=1000,
            justify="left"
        )
        q_text.pack(fill="x", padx=15, pady=10)

        if question["type"] == "MCQ":
            self.user_answers[num] = tk.StringVar()

            for i, option in enumerate(question["options"]):
                rb = ctk.CTkRadioButton(
                    q_frame,
                    text=option,
                    variable=self.user_answers[num],
                    value=option,
                    font=("Helvetica", 14),
                    text_color="white",
                    fg_color=self.button_color,
                )
                rb.pack(anchor="w", padx=40, pady=5)

        elif question["type"] in ["Very Short", "Short(I)"]:
            entry = ctk.CTkEntry(
                q_frame,
                font=("Helvetica", 14),
                height=40,
                width=800
            )
            entry.pack(padx=15, pady=10, fill="x")
            self.user_answers[num] = entry

        else:
            textbox = ctk.CTkTextbox(
                q_frame,
                font=("Helvetica", 14),
                height=150 if question["type"] == "Long Answer" else 100,
                width=800
            )
            textbox.pack(padx=15, pady=10, fill="both")
            self.user_answers[num] = textbox

    def submit_test(self):
        """Submit and grade test"""
        answers = {}
        for num, widget in self.user_answers.items():
            if isinstance(widget, tk.StringVar):
                answers[num] = widget.get()
            elif isinstance(widget, ctk.CTkEntry):
                answers[num] = widget.get()
            else:
                answers[num] = widget.get("1.0", "end-1c")

        self.clear_screen()

        loading_label = ctk.CTkLabel(
            self,
            text="Please wait while your test is being graded...\n\nEvaluating your answers...",
            font=("Helvetica", 18),
            text_color="white"
        )
        loading_label.pack(expand=True)

        self.grade_progress = ctk.CTkProgressBar(self, width=400)
        self.grade_progress.pack(pady=20)
        self.grade_progress.set(0)

        def grading_thread():
            try:
                self.after(0, lambda: self.grade_progress.set(0.3))
                time.sleep(0.1)

                self.results = self.test_grader.grade_test(
                    self.test_data,
                    answers
                )

                self.after(0, lambda: self.grade_progress.set(1.0))
                time.sleep(0.1)

                self.after(500, self.show_results_screen)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to grade test: {str(e)}")
                self.after(0, self.show_upload_screen)

        thread = threading.Thread(target=grading_thread, daemon=True)
        thread.start()

    def show_results_screen(self):
        """Screen 3: Results"""
        if not self.results:
            return

        self.clear_screen()

        header = ctk.CTkFrame(self, fg_color=self.panel_color, height=120)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="Test Results",
            font=("Helvetica", 22, "bold"),
            text_color="white"
        )
        title.pack(pady=(15, 5))

        score_text = f"{self.results['total_score']}/{self.results['total_marks']}"
        percentage = (self.results['total_score'] / self.results['total_marks']) * 100

        score_label = ctk.CTkLabel(
            header,
            text=f"Score: {score_text} ({percentage:.1f}%)",
            font=("Helvetica", 20, "bold"),
            text_color=self.correct_color if percentage >= 50 else self.wrong_color
        )
        score_label.pack(pady=5)

        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=self.bg_color,
            corner_radius=10
        )
        scroll_frame.pack(expand=True, fill="both", padx=20, pady=10)

        for i, result in enumerate(self.results['questions'], 1):
            self.create_result_widget(scroll_frame, result, i)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        download_btn = ctk.CTkButton(
            button_frame,
            text="Download Results",
            font=("Helvetica", 14, "bold"),
            fg_color=self.button_color,
            hover_color="#357ABD",
            height=45,
            width=180,
            command=self.download_results
        )
        download_btn.pack(side="left", padx=5)

        retake_btn = ctk.CTkButton(
            button_frame,
            text="Retake Test",
            font=("Helvetica", 14, "bold"),
            fg_color=self.button_color,
            hover_color="#357ABD",
            height=45,
            width=180,
            command=self.retake_test
        )
        retake_btn.pack(side="left", padx=5)

        new_test_btn = ctk.CTkButton(
            button_frame,
            text="New Test",
            font=("Helvetica", 14, "bold"),
            fg_color=self.button_color,
            hover_color="#357ABD",
            height=45,
            width=180,
            command=self.show_upload_screen
        )
        new_test_btn.pack(side="left", padx=5)

    def create_result_widget(self, parent, result, num):
        """Create widget for a single result"""
        is_correct = result['marks_earned'] == result['marks_possible']

        border_color = self.correct_color if is_correct else (
            self.wrong_color if result['marks_earned'] == 0 else "#FFA500"
        )

        r_frame = ctk.CTkFrame(
            parent,
            fg_color=self.panel_color,
            corner_radius=10,
            border_width=3,
            border_color=border_color
        )
        r_frame.pack(fill="x", pady=10, padx=10)

        header_text = f"Q{num}. {result['type']} - {result['marks_earned']}/{result['marks_possible']} marks"
        header = ctk.CTkLabel(
            r_frame,
            text=header_text,
            font=("Helvetica", 14, "bold"),
            text_color=border_color,
            anchor="w"
        )
        header.pack(fill="x", padx=15, pady=(15, 5))

        q_label = ctk.CTkLabel(
            r_frame,
            text=f"Question: {result['question']}",
            font=("Helvetica", 14),
            text_color="white",
            anchor="w",
            wraplength=1000,
            justify="left"
        )
        q_label.pack(fill="x", padx=15, pady=5)

        user_ans = ctk.CTkLabel(
            r_frame,
            text=f"Your Answer: {result['user_answer']}",
            font=("Helvetica", 14),
            text_color="#AAAAAA",
            anchor="w",
            wraplength=1000,
            justify="left"
        )
        user_ans.pack(fill="x", padx=15, pady=5)

        correct_ans = ctk.CTkLabel(
            r_frame,
            text=f"Correct Answer: {result['correct_answer']}",
            font=("Helvetica", 14),
            text_color=self.correct_color,
            anchor="w",
            wraplength=1000,
            justify="left"
        )
        correct_ans.pack(fill="x", padx=15, pady=5)

        if result.get('feedback'):
            feedback = ctk.CTkLabel(
                r_frame,
                text=f"Feedback: {result['feedback']}",
                font=("Helvetica", 12, "italic"),
                text_color="#FFAA00",
                anchor="w",
                wraplength=1000,
                justify="left"
            )
            feedback.pack(fill="x", padx=15, pady=(5, 15))

    def retake_test(self):
        """Retake the same test"""
        self.is_retake = True
        self.user_answers = {}
        self.show_test_screen()

    def download_results(self):
        """Download results as CSV"""
        if not self.results:
            return

        filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=filename
        )

        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("Question,Type,Marks Earned,Marks Possible,User Answer,Correct Answer,Feedback\n")
                    for i, result in enumerate(self.results['questions'], 1):
                        f.write(f'"{i}","{result["type"]}","{result["marks_earned"]}","{result["marks_possible"]}",'
                               f'"{result["user_answer"]}","{result["correct_answer"]}","{result.get("feedback", "")}"\n')
                    f.write(f'\nTotal Score,{self.results["total_score"]}/{self.results["total_marks"]}')

                messagebox.showinfo("Success", f"Results saved to {os.path.basename(filepath)}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")


if __name__ == "__main__":
    app = AITestMaker()
    app.mainloop()

