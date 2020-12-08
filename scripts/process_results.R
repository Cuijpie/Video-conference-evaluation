setwd("~/Documents/Video-conference-evaluation")
library(dplyr)
library(ggplot2)

###########################
video_files <- list.files(pattern = "system-metrics-audio-video.csv$", recursive = TRUE)
audio_files <- list.files(pattern = "system-metrics-audio-only.csv$", recursive = TRUE)
line_color <- c("#03045e", "#006600")
prob <- c(0.25, 0.75)

exps <- c(video_files, audio_files)
###########################

data <- NA

for (file in system_files) {
  df = read.csv(file)[1:240,]
  data <- rbind(data, df)
}

data <- as.data.frame(data)

data <- data[complete.cases(data), ]
avg <- setNames(aggregate(data[, 3], list(data$X), mean), c("Index", "Packet_Count"))
quantiles <- dplyr::summarise(group_by(data, X),
                              Qlower = quantile(avg_packet_len, probs=prob[1]),
                              Qupper = quantile(avg_packet_len, probs=prob[2]))


graph <- ggplot() +
  geom_line(data=avg, aes(y=Packet_Count, x=Index), color=line_color[1]) +
  geom_ribbon(aes_string(ymin=quantiles$Qlower, ymax=quantiles$Qupper, x=avg$Index), fill=line_color[1], color=line_color[1], alpha=0.2, size=0.2) +
  scale_y_continuous("Average packet length per second", limits=c(0,800)) +
  scale_x_continuous("Time in seconds") +
  ggtitle("Average packet length per second for video + audio")