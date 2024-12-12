import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
import platform

class SRRProcessorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.output_directory = ""
        self.script_filename = ""
        self.app_directory = os.path.dirname(os.path.abspath(__file__))

    def init_ui(self):
        # Set up the layout
        layout = QVBoxLayout()

        # Instruction Label
        self.label = QLabel('Paste SRR accession codes (one per line):')
        layout.addWidget(self.label)

        # Textbox for SRR codes
        self.text_input = QTextEdit(self)
        layout.addWidget(self.text_input)

        # Threads selection label
        self.threads_label = QLabel('Select number of threads (default is 4):')
        layout.addWidget(self.threads_label)

        # Input field for threads
        self.threads_input = QLineEdit(self)
        self.threads_input.setText("4")  # Default number of threads is 4
        layout.addWidget(self.threads_input)

        # Output directory button
        self.output_button = QPushButton('Select Output Directory', self)
        self.output_button.clicked.connect(self.select_output_directory)
        layout.addWidget(self.output_button)

        # Label to show selected output directory
        self.output_label = QLabel('No directory selected')
        layout.addWidget(self.output_label)

        # Generate Script button
        self.generate_button = QPushButton('Generate Script', self)
        self.generate_button.clicked.connect(self.generate_script)
        layout.addWidget(self.generate_button)

        # Run Script button
        self.run_button = QPushButton('Run Script', self)
        self.run_button.clicked.connect(self.run_script)
        layout.addWidget(self.run_button)

        # Text area to show success/error messages (log output)
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)  # Make it read-only to show log messages
        layout.addWidget(self.log_output)

        # Set layout and window properties
        self.setLayout(layout)
        self.setWindowTitle('SRR Processor')
        self.setGeometry(300, 300, 400, 500)

    def select_output_directory(self):
        # Open a file dialog to select the output directory
        self.output_directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if self.output_directory:
            self.output_label.setText(f"Selected Directory: {self.output_directory}")
        else:
            self.output_label.setText("No directory selected")

    def generate_script(self):
        # Clear the log output before generating script
        self.log_output.clear()

        # Get SRR codes from the text box
        srr_codes = self.text_input.toPlainText().strip().splitlines()
        num_threads = self.threads_input.text()

        if not srr_codes:
            self.log_output.append("Input Error: Please paste SRR accession codes.")
            return

        if not num_threads.isdigit():
            self.log_output.append("Input Error: Please enter a valid number for threads.")
            return

        if not self.output_directory:
            self.log_output.append("Directory Error: Please select an output directory.")
            return

        # Determine the script extension and file format based on the operating system
        if platform.system() == "Windows":
            self.script_filename = os.path.join(self.output_directory, "process_srr.cmd")
            is_windows = True
        else:
            self.script_filename = os.path.join(self.output_directory, "process_srr.sh")
            is_windows = False

        try:
            with open(self.script_filename, 'w') as script_file:
                if not is_windows:
                    script_file.write("#!/bin/bash\n\n")
                    script_file.write("# Add app directory to PATH\n")
                    script_file.write(f'export PATH="{self.app_directory}:$PATH"\n\n')
                else:
                    script_file.write("@echo off\n")
                    script_file.write("REM Add app directory to PATH\n")
                    script_file.write(f'set "PATH={self.app_directory};%PATH%"\n\n')

                for srr in srr_codes:
                    srr = srr.strip()
                    if srr:
                        # Prepare the sorted BAM file path
                        output_sorted_bam = os.path.join(self.output_directory, f"{srr}.sorted.bam")

                        if is_windows:
                            # Write commands for Windows (CMD batch file)
                            script_file.write(f"sam-dump.exe {srr} | samtools.exe sort --no-PG -@{num_threads} -o \"{output_sorted_bam}\"\n")
                            script_file.write(f"samtools.exe index -@{num_threads} \"{output_sorted_bam}\"\n")
                        else:
                            # Write commands for Linux/macOS (Bash script)
                            script_file.write(f"sam-dump {srr} | samtools sort --no-PG -@{num_threads} -o \"{output_sorted_bam}\"\n")
                            script_file.write(f"samtools index -@{num_threads} \"{output_sorted_bam}\"\n")

            # Make the script executable for Linux/macOS
            if not is_windows:
                os.chmod(self.script_filename, 0o755)

            self.log_output.append(f"Success: Script generated at {self.script_filename}")

        except Exception as e:
            self.log_output.append(f"Error: Failed to generate script: {e}")

    def run_script(self):
        if not self.script_filename:
            self.log_output.append("Error: No script has been generated yet.")
            return

        try:
            env = os.environ.copy()
            env['PATH'] = f"{self.app_directory}{os.pathsep}{env['PATH']}"

            if platform.system() == "Windows":
                subprocess.Popen(["cmd", "/c", self.script_filename], cwd=self.output_directory, env=env)
            else:
                subprocess.Popen(["bash", self.script_filename], cwd=self.output_directory, env=env)
            
            self.log_output.append(f"Script execution started: {self.script_filename}")
        except Exception as e:
            self.log_output.append(f"Error: Failed to run script: {e}")

# Main function to run the app
if __name__ == '__main__':
    app = QApplication(sys.argv)
    srr_processor = SRRProcessorApp()
    srr_processor.show()
    sys.exit(app.exec_())