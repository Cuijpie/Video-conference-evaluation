setwd("~/Documents/Video-conference-evaluation")
library(dplyr)
library(ggplot2)
library(reshape2)
###########################
path = "results/"
files = c('Zoom-throttle.csv', 'Teams-throttle.csv', 'Discord-throttle.csv')

software <- c('Zoom', 'Teams', 'Discord')
###########################

data <- NA

for (i in 1:length(software)) {
  file_name <- files[[i]]
  df = read.csv(paste(path, file_name, sep=''))[1:599,]
  
  if (i == 1) {df = subset(df, select = -c(cpu_limit))}
  
  df$software <- software[[i]]
  
  data <- rbind(data, df)
  data = data[-1,]
}

data <- data %>% mutate(cpu_usage = cpu_usage/100)
data <- data %>% mutate(bandwidth = bandwidth_calc / 1000) #bandwidth in kbytes
data <- data %>% mutate(bandwidth_limit = bandwidth_limit / 1000) #bandwidth in kbytes
data <- data %>% mutate(avg_packet_len = avg_packet_len) #bandwidth in kbytes
data <- transform(data, bandwidth_limit = ifelse(bandwidth_limit == 0, NA, bandwidth_limit))

dat <- data.frame(data$X, data$bandwidth_limit, data$bandwidth, data$packet_count, data$avg_packet_len, data$cpu_usage, data$software)

dat.m <- melt(dat, id.var=c('data.software', 'data.X'))

facet_labels <- list(
  'data.bandwidth_limit' = "Bandwidth limit in KiloBytes per second.",
  'data.bandwidth' = "Received number of kiloBytes.",
  'data.packet_count' = "Number of packets received per second",
  'data.avg_packet_len' = "Average packet size in bytes per second",
  'data.cpu_usage' = "Number of CPU cores used per second"
)

facet_labeller <- function(variable, value) {
  return(facet_labels[value])
}

p <- ggplot(dat.m, aes(data.X, value, colour = variable)) +
  geom_line(data=filter(dat.m, variable=='data.bandwidth_limit'), aes(color=data.software)) +
  geom_smooth(data=filter(dat.m, variable!='data.bandwidth_limit'), aes(color=data.software)) +
  facet_wrap(~ variable, ncol = 1, scales = "free_y", labeller = facet_labeller) + 
  scale_x_continuous("Time(s)", breaks = seq(0, 600, 60)) +
  scale_y_continuous(expand = c(0, 0), limits = c(0, NA)) +
  theme(legend.title = element_blank(),
        legend.position="bottom",
        axis.title.y.left = element_blank()) +
  guides(fill = guide_legend(reverse=TRUE)) +
  scale_color_discrete(breaks=c("Zoom", "Teams", "Discord"))

print(p)