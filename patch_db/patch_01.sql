CREATE TABLE `project-ppt`.`hoax_detection_results` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `input_text` TEXT NOT NULL,
  `process_category` ENUM('summarization', 'not summarization') NOT NULL DEFAULT 'not summarization',
  `output_label` ENUM('hoax', 'not hoax') NOT NULL,
  `date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  PRIMARY KEY (`id`));