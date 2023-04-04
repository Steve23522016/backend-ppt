ALTER TABLE `project-ppt`.`hoax_detection_results` 
ADD COLUMN `summarization_result` TEXT NULL DEFAULT NULL AFTER `process_category`;
