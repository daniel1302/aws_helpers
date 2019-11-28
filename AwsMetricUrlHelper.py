class AwsMetricUrlHelper:
    def __init__(self, region):
        self.aws_cloudwatch_home_url = "https://console.aws.amazon.com/cloudwatch/home"
        self.graphVersion = "metricsV2"
        self.region = region

    
    def _aws_param_encode(self, value):
        value = urllib.parse.quote(value)
        return str(value).replace('%', '*')


    def _aws_param_name(self, name, first=False):
        result = ''
        if not first:
            result += '~'
        result += self._aws_param_encode(name)

        return result


    def _aws_string(self, value):
        return "~'" + self._aws_param_encode(value)


    def _aws_bool(self, value):
        if not value:
            return '~false'

        return '~true'

    
    def _aws_number(self, value):
        return '~' + str(value)


    def _aws_join(self, aws_list):
        return ''.join(aws_list)


    def _aws_list(self, items):
        if isinstance(items, list):
            items_str =  self._aws_join([ str(v) for v in items ])
        elif isinstance(items, dict):
            items_str =  self._aws_join([ str(k) + str(items[k]) for k in items.keys() ])
        else:
            return ''

        return self._aws_join(['~(', items_str, ')'])


    def _encode_metrics(self, metric_list):
        metrics = []
        default_stat = 'Average'

        for metric_data in metric_list:
            if 'Namespace' not in metric_data or 'MetricName' not in metric_data:
                continue

            dimensions = {}
            if 'Dimensions' in metric_data and metric_data['Dimensions']:
                dimensions = metric_data['Dimensions']

            stat_name = default_stat
            if 'Statistic' in metric_data:
                stat_name = metric_data['Statistic']
            
            metrics.append(self._aws_list([
                self._aws_string(metric_data['Namespace']),
                self._aws_string(metric_data['MetricName']),
                self._aws_join([ self._aws_string(k) + self._aws_string(dimensions[k]) for k in dimensions.keys() ]),
                self._aws_list({
                    self._aws_param_name('stat', True): self._aws_string(stat_name.capitalize())
                })
            ]))

        return self._aws_join(metrics)


    def url(self, metrics_list, period, time_diff_hours):
        diff_time = int((3600*time_diff_hours)/2)
        current_time = datetime.datetime.now()   
        start_time = strftime("%Y-%m-%dT%H:%M:%S", (current_time-datetime.timedelta(seconds=diff_time)).timetuple())
        end_time = strftime("%Y-%m-%dT%H:%M:%S", (current_time+datetime.timedelta(seconds=diff_time)).timetuple())

        encoded_params = self._aws_list({
            self._aws_param_name('view', True): self._aws_string('timeSeries'),
            self._aws_param_name('period'): self._aws_number(period),
            self._aws_param_name('stacked'): self._aws_bool(False),
            self._aws_param_name('region'): self._aws_string(self.region),
            self._aws_param_name('start'): self._aws_string(start_time),
            self._aws_param_name('end'): self._aws_string(end_time),
            self._aws_param_name('metrics'): self._aws_list([ self._encode_metrics(metrics_list) ]),
        })
        
        return self._aws_join([
            self.aws_cloudwatch_home_url,
            '?region=' + self.region,
            '#' + self.graphVersion,
            ':graph=',
            encoded_params 
        ])
