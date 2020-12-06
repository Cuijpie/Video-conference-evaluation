setwd("~/Documents/Video-conference-evaluation")
library(dplyr)
library(ggplot2)

###########################
path = "results/"

zoom_files <- c('Zoom-audio+video.csv', 'Zoom-video.csv', 'Zoom-audio.csv')
teams_files <- c('Teams-audio+video.csv','Teams-video.csv','Teams-audio.csv')
discord_files <- c('Discord-Audio+Video.csv','Discord-video.csv','Discord-audio.csv')

software <- c('Zoom', 'Teams', 'Discord')
files <- list(zoom_files, teams_files, discord_files)

line_color <- c("#03045e", "#006600")
prob <- c(0.25, 0.75)
###########################

data <- NA

for (i in 1:length(software)) {
  for (j in 1:length(files[[i]])) {
    file_name <- files[[i]][j]
    df = read.csv(paste(path, file_name, sep=''))[1:3000,]
    df$software <- software[[i]]
    x <- gsub('.csv', '', file_name)
    df$Experiment <- gsub('-', ': ',x)
    
    data <- rbind(data, df)
  }
}

data <- as.data.frame(data)[-1,]
data <- data %>% mutate(cpu_usage = cpu_usage / 100)
data <- data %>% mutate(bandwidth = bandwidth_calc / 1000)
variables <- c('packet_count', 'avg_packet_len', 'bandwidth', 'cpu_usage')



for (var in variables) {
  p <- ggplot(data, aes(x=.data[[var]], y=Experiment, fill=Experiment)) + 
    #geom_violin(trim = FALSE) + 
    geom_boxplot(width = 0.6, outlier.size = -1, ylim=c(0.8,3.2)) + 
    stat_summary(fun=mean, geom="point", size=2, color="white", show_guide=FALSE) + 

    scale_fill_brewer(palette="Dark2") + 
   
    theme(aspect.ratio = 5/10,
      legend.title = element_text(size = 14),
      legend.text = element_text(size = 12),
          axis.title.y = element_blank(),
          axis.text.y = element_blank(),
          axis.title.x = element_text(color = "black", size = 12),
          axis.text.x = element_text(color = "black", size = 12)) +
    guides(fill = guide_legend(reverse=TRUE))
  
  if (var == "packet_count") {
    p <- p + scale_x_continuous("Number of packets", limits=c(0, quantile(data[[var]], probs=0.98))) + theme(legend.position = "none")
  } else if (var == 'avg_packet_len') {
    p <- p + scale_x_continuous('Average packet size in bytes', limits=c(0, quantile(data[[var]], probs=0.9999))) + theme(legend.position = "none")
  } else if (var == 'bandwidth') {
    p <- p + scale_x_continuous('Average kilobytes[1000 bytes] received', limits=c(0, quantile(data[[var]], probs=0.99985))) + theme(legend.position = "none")
  } else if (var == 'cpu_usage') {
    p <- p + scale_x_continuous('Average number of CPU cores used', limits=c(0, quantile(data[[var]], probs=0.99)))
  }
  #print(p)
  ggsave(paste(var,".pdf", sep=''))
}
