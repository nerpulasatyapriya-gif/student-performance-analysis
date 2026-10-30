CREATE DATABASE IF NOT EXISTS student_performance
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE student_performance;

CREATE TABLE IF NOT EXISTS students (
  student_id INT AUTO_INCREMENT PRIMARY KEY,
  roll_no VARCHAR(30) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  section VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS subjects (
  subject_id INT AUTO_INCREMENT PRIMARY KEY,
  subject_name VARCHAR(100) NOT NULL UNIQUE,
  max_marks DECIMAL(7,2) NOT NULL,
  pass_marks DECIMAL(7,2) NOT NULL,
  CONSTRAINT chk_max_marks CHECK (max_marks > 0),
  CONSTRAINT chk_pass_marks CHECK (pass_marks >= 0 AND pass_marks <= max_marks)
);

CREATE TABLE IF NOT EXISTS marks (
  mark_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  subject_id INT NOT NULL,
  assessment VARCHAR(80) NOT NULL,
  marks_obtained DECIMAL(7,2) NOT NULL,
  CONSTRAINT fk_marks_student FOREIGN KEY (student_id) REFERENCES students(student_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_marks_subject FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
    ON DELETE CASCADE,
  CONSTRAINT uq_student_subject_assessment UNIQUE (student_id, subject_id, assessment),
  CONSTRAINT chk_marks_nonnegative CHECK (marks_obtained >= 0)
);

-- Optional starter subjects. Remove these INSERTs if you prefer an empty database.
INSERT IGNORE INTO subjects (subject_name, max_marks, pass_marks) VALUES
('Mathematics', 100, 40),
('Computer Networks', 100, 40),
('Programming', 100, 40),
('Database Systems', 100, 40);
