
#setwd("~/Documents/Video-conference-evaluation")
library(dplyr)
library(ggplot2)
library(reshape2)
library(cowplot)
###########################
path = "results/"
files = c('zoom-audio.csv', 'zoom-classroom.csv')

protocol <- c('One-on-One', 'Classroom Screensharing')
###########################

data <- NA

for (i in 1:length(protocol)) {
  file_name <- files[[i]]
  df = read.csv(paste(path, file_name, sep=''))[1:2861,]
  df$protocol <- protocol[[i]]
  
  data <- rbind(data, df)
  
}
data = data[-1,]

data <- data %>% mutate(cpu_usage = cpu_usage/100)
data <- data %>% mutate(bandwidth = bandwidth_calc / 1000) #bandwidth in kbytes
data <- data %>% mutate(bandwidth_limit = bandwidth_limit / 1000) #bandwidth in kbytes
data <- data %>% mutate(avg_packet_len = avg_packet_len) #bandwidth in kbytes
data$protocol <- factor(data$protocol, levels=c("One-on-One", "Classroom Screensharing"), ordered=TRUE)
dat <- data.frame(data$X, data$bandwidth, data$packet_count, data$avg_packet_len, data$cpu_usage, data$protocol)

dat.m <- melt(dat, id.var=c('data.protocol', 'data.X'))

facet_labels <- list(
  'data.bandwidth' = "Number of KiloBytes received per second.",
  'data.packet_count' = "Number of packets received per second",
  'data.avg_packet_len' = "Average packet size in bytes per second",
  'data.cpu_usage' = "Number of CPU cores used per second"
)

dat.m <- dat.m %>%
  group_by(data.protocol) %>%
  # mutate(markers = ifelse(data.protocol == 'One-on-One'& (row_number() + 200) %% 300 == 0, value, NA))
  mutate(markers = ifelse((data.protocol == 'One-on-One'& (row_number() + 200) %% 300 == 0) | ((data.protocol != 'One-on-One'& (row_number() + 50) %% 300 == 0)), value, NA))

p <- ggplot(dat.m, aes(data.X, value, color = data.protocol)) +
  geom_line(aes(linetype = data.protocol), size=0.5) +
  geom_point(aes(y=markers, shape= data.protocol, color = data.protocol), size=3) +
  facet_wrap(~ variable, ncol = 1, scales = "free_y", labeller = facet_labeller) +
  # scale_shape_manual(values=c(21, 24))+
  scale_x_continuous("Time (s)", breaks = seq(0, 2000, 1000)) +
  scale_y_log10() +
  # scale_y_continuous(expand = c(0, 1), limits = c(0, NA)) +
  guides(fill = guide_legend(reverse=TRUE)) +
  scale_color_discrete(breaks=c("One-on-One", "Classroom Screensharing")) +
  theme_half_open() +
  theme(strip.background=element_rect(fill='white', color="black")) +
  background_grid(major = "y") +
  theme(legend.title = element_blank(),
        legend.position="bottom",
        axis.title.y.left = element_blank(),
        text = element_text(size = 15),
        strip.text.x = element_text(size = 15))

#last_plot() + aes(group=rev(variable))
p
ggsave("../results/oneonone-vs-classroom.pdf", width = 6, height= 5)