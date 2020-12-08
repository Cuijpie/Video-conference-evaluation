setwd("~/Documents/Video-conference-evaluation")
library(dplyr)
library(ggplot2)
library(reshape2)
###########################
path = "results/"
files = c('Zoom-audio+video.csv','zoom-wifi4.csv', 'zoom-wifi5.csv', 'zoom-4G.csv')

protocol <- c('Ethernet', 'Wi-Fi 4', 'Wi-Fi 5', '4G LTE')
###########################

data <- NA

for (i in 1:length(protocol)) {
  file_name <- files[[i]]
  df = read.csv(paste(path, file_name, sep=''))[1:590,]
  df$protocol <- protocol[[i]]
  
  data <- rbind(data, df)
  
}
data = data[-1,]

data <- data %>% mutate(cpu_usage = cpu_usage/100)
data <- data %>% mutate(bandwidth = bandwidth_calc / 1000) #bandwidth in kbytes
data <- data %>% mutate(bandwidth_limit = bandwidth_limit / 1000) #bandwidth in kbytes
data <- data %>% mutate(avg_packet_len = avg_packet_len) #bandwidth in kbytes
data$protocol <- factor(data$protocol, levels=c("Ethernet", "Wi-Fi 4", "Wi-Fi 5", "4G LTE"), ordered=TRUE)
dat <- data.frame(data$X, data$bandwidth, data$packet_count, data$avg_packet_len, data$cpu_usage, data$protocol)

dat.m <- melt(dat, id.var=c('data.protocol', 'data.X'))

facet_labels <- list(
  'data.bandwidth' = "Number of KiloBytes received per second.",
  'data.packet_count' = "Number of packets received per second",
  'data.avg_packet_len' = "Average packet size in bytes per second",
  'data.cpu_usage' = "Number of CPU cores used per second"
)

p <- ggplot(dat.m, aes(data.protocol, y=value, colour = variable)) +
  geom_boxplot(width = 0.7, outlier.size = -1, aes(color=data.protocol)) +
  stat_summary(fun=mean, geom="point", size=2, color="black", aes(group=data.protocol)) + 
  facet_wrap(~ variable, ncol = 1, scales = "free_y", labeller = facet_labeller) + 
  scale_y_continuous(expand = c(0, 0), limits = c(0, NA)) +
  guides(fill = guide_legend(reverse=TRUE)) +
  scale_color_discrete(breaks=c("Ethernet", "Wi-Fi 4", "Wi-Fi 5", "4G LTE")) +
  theme(legend.position = "none") +
  xlab("Wired/Wireless Network Procotol") +
  ylab("")

print(p)
ggsave("network.pdf")
