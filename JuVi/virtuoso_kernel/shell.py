"""
Python wrapper for Virtuoso shell.

To be used in conjunction with IPython/Jupyter.
"""
import zmq
import json
from jupyter_core.paths import jupyter_data_dir
import re
import colorama

class VirtuosoExceptions(Exception):
    """
    To handle errors throws by the virtuoso shell
    """
    def __init__(self, value):
        self.value = value
        super(VirtuosoExceptions, self).__init__(value)

    def __str__(self):
        return repr(self.value)


class VirtuosoShellClient(object):
    """
    This is the client that talks to dfII's python server
    """
    def __init__(self, port=None):
        super(VirtuosoShellClient, self).__init__()
        self.port = None
        self.host = None
        self.context = None
        self.socket = None
        self.init()

    def init(self):
        # Get connection info from the PyLL JSON file
        CONN_FILE = jupyter_data_dir() + "/runtime/" + "virtuoso-pyll.json"
        with open(CONN_FILE, "r") as COF:
            self.host, self.port = json.load(COF)
        # Connection info will come from a JSON file generated by the dfII/PyLL
        # server. So, read JSON to figure out the connection info.
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://%s:%d" % (self.host, self.port))

    def write(self, payload):
        #TODO: make sure the payload type is correct
        self.socket.send_string(payload)

    def read(self):
        return self.socket.recv().decode()

    def read_parsed(self):
        return json.loads(self.socket.recv().decode())

    def close(self):
        # Close socket
        self.socket.close()

class VirtuosoShell(object):
    """
    This class gives a python interface to the Virtuoso shell.
    """
    _banner = None
    _version_re = None
    _output = ""

    @property
    def banner(self):
        """
        Virtuoso shell's banner
        """
        self._shell.write("getVersion()")
        self._banner = self._shell.read_parsed()['result']
        return self._banner

    @property
    def language_version(self):
        """
        Language version
        """
        __match__ = self._version_re.search(self.banner)
        return __match__.group(1)

    @property
    def output(self):
        """
        Last output returned by the shell
        """
        return self._output

    def __init__(self, *args, **kwargs):
        super(VirtuosoShell, self).__init__(*args, **kwargs)
        self.prompt = [re.compile(r'\r\n<<pyvi>> $'),
                       re.compile(r'^<<pyvi>> $')]
        self._shell_available_re = re.compile(r'"__jupyter_kernel_ready__"'
                                              r'[\s\S]+')
        self._version_re = re.compile(r'version (\d+(\.\d+)+)')
        self._multiline_re = re.compile(r'[^\\]\n')
        self._error_re = re.compile(r'^([\s\S]*?)\*Error\*'
                                    r'(.+)(\s*)([\s\S]*)')
        self._open_braces_re = re.compile(r'\{')
        self._close_braces_re = re.compile(r'\}')
        self._open_paren_re = re.compile(r'\(')
        self._close_paren_re = re.compile(r'\)')
        self._dbl_quote_re = re.compile(r'"')
        self._output_prompt_re = re.compile(r'<<pyvi>> ')
        self._object_prop_re = re.compile(r'(\w+?)\s*([-~]>)(\w*?)$')
        self._object_prop_list_re = re.compile(r'\((\w+?)\)\s*([-~]>)(\w*?)$')
        self._var_name_re = re.compile(r'\s*(\w+)$')
        self.match_dict = {self._object_prop_re: lambda _match: '%s%s?' %
                           (_match.group(1), _match.group(2)),
                           self._object_prop_list_re: lambda _match:
                           'car(%s)%s?' % (_match.group(1), _match.group(2)),
                           self._var_name_re: lambda _match:
                           'listFunctions("^%s" t)\r\nlistVariables("^%s")' %
                           (_match.group(1), _match.group(1))}
        self._start_virtuoso()

    def _start_virtuoso(self):
        """
        Connect to the virtuoso shell
        """
        self._shell = VirtuosoShellClient()

    def _parse_output(self):
        """
        Parse the virtuoso shell's output and handle error.

        #TODO: Can I use the skill debugger somehow?

        In case of error, set status to a tuple of the form :
            (etype, evalue, tb)
        else, set to None
        """
        err_out = self._output['error']
        warn_out = self._output['warning']
        info_out = self._output['info']
        res_out = self._output['result']
        full_out = ""
        _err_match = None

        if err_out is not None:
            full_out += ("%s%s%s%s%s\n" % (colorama.Style.BRIGHT,
                         colorama.Fore.RED, err_out, colorama.Fore.RESET,
                         colorama.Style.NORMAL))
            _err_match = self._error_re.search(err_out)
        if warn_out is not None:
            full_out += ("%s%s%s%s%s\n" % (colorama.Style.BRIGHT,
                         colorama.Fore.YELLOW, warn_out, colorama.Fore.RESET,
                         colorama.Style.NORMAL))
        if info_out is not None:
            full_out += ("%s\n" % info_out)
        if res_out is not None:
            full_out += res_out

        self._output = full_out

        # If the shell reported any errors, throw exception
        if _err_match is not None:
            _exec_error = ("Error", 1, _err_match.group(2))
            raise VirtuosoExceptions(_exec_error)

        #self._exec_error = None
        #_err_match = self._error_re.search(self._output)
        #if _err_match is not None:
        #    self._exec_error = ("Error", 1, _err_match.group(2))

        ## number the output line
        #_output_list = [_line.rstrip() for _line in
        #                self._output_prompt_re.split(self._output) if
        #                _line.rstrip() != '']
        #_out_num = 1
        #_color = colorama.Fore.YELLOW
        #self._output = ''
        #_single_line = (len(_output_list) == 1)
        #for _oline in _output_list:
        #    if self._error_re.search(_oline) is not None:
        #        _color = colorama.Fore.RED
        #        if(not _single_line):
        #            self._output += ('%s%s%d> %s%s%s\n' %
        #                             (colorama.Style.BRIGHT, _color, _out_num,
        #                              _oline, colorama.Fore.RESET,
        #                              colorama.Style.NORMAL))
        #        else:
        #            self._output += ('%s%s%s%s%s\n' % (colorama.Style.BRIGHT,
        #                                               _color, _oline,
        #                                               colorama.Fore.RESET,
        #                                               colorama.Style.NORMAL))
        #    else:
        #        _color = colorama.Fore.YELLOW
        #        if(not _single_line):
        #            self._output += '%s%d>%s %s\n' % (_color, _out_num,
        #                                              colorama.Fore.RESET,
        #                                              _oline)
        #        else:
        #            self._output += '%s\n' % (_oline)
        #    _out_num += 1
        #self._output = self.output.rstrip()
        ## If the shell reported any errors, throw exception
        #if self._exec_error is not None:
        #    raise VirtuosoExceptions(self._exec_error)

    def _pretty_introspection(self, info, keyword):
        import re
        # Optional keywords
        info = re.sub(r'(\?\w+)', r'%s\1%s' % (colorama.Fore.YELLOW,
                                               colorama.Fore.RESET), info,
                      count=0)
        # Required arguments
        info = re.sub(r'(\s*)(%s\()([\r\n]*)([\w\s]+)([\s\S]+)' % keyword,
                      r'\1\2\3%s\4%s\5' % (colorama.Fore.GREEN,
                                           colorama.Fore.RESET), info)
        # Function name
        info = re.sub(r'(%s)(\()' % keyword,
                      r'%s\1%s\2' % (colorama.Fore.BLUE,
                                     colorama.Fore.RESET),
                      info, count=0)
        return info[:-1]

    def run_raw(self, code):
        """
        Send the code as it is.

        This is useful for executing single functions. Output is not
        post-processed in this function.
        """
        self._shell.write(code)
        self._output = self._shell.read()

    def run_cell(self, code):
        """
        Executes the 'code'.

        We need to wrap a block of SKILL code in `prog` or equivalently in
        `{...}` for `evalstring` to work correctly on the dfII side.
        """

        if self._multiline_re.search(code):
            self._shell.write("{" + code + "}")
        else:
            self._shell.write(code)
        self.wait_ready()

        # Check the output and throw exception in case of error
        self._parse_output()

        return self.output

    def get_matches(self, code_line):
        """
        Return a list of functions and variables matching the line's end or
        in case of '->' or '~>', a list of attributes.
        """
        _cmd = None
        _token = ''
        _match_list = []
        _match = self._object_prop_re.search(code_line)
        _raw_mode = True
        if(_match is None):
            _match = self._object_prop_list_re.search(code_line)
        if(_match is None):
            _match = self._var_name_re.search(code_line)
            _raw_mode = False
        if(_match is not None):
            _cmd = self.match_dict[_match.re](_match)
            _token = _match.group(1)
            self.run_raw(_cmd)
            _output = json.loads(self._output)['result']
            if _output != u'nil':
                _output = _output.replace('(', ' ')
                _output = _output.replace(')', ' ')
                _output = _output.replace('nil', ' ')
                _match_list = _output.split()
                if(len(_match.groups()) == 3):
                    # when there is part of an attr.
                    _token = _match.group(3)
                    if(_token != ''):
                        _match_list = [_match for _match in _match_list if
                                       _match.startswith(_token)]

        return((_match_list, _token))

    def get_info(self, token):
        """
        Returns info on the requested object

        """
        # TODO: get info on variables also
        # Make sure that only valid function/variable names are used
        if token.rstrip() != '':
            token = re.match(r'(\S+?)\s*$', token).group(1)
        _cmd = 'help(%s)' % token
        self.run_raw(_cmd)
        _pay = json.loads(self._output)
        # Handle cases where no help is available
        if (_pay['info'] is None) or (_pay['result'] == "nil"):
            return ""
        else:
            return (self._pretty_introspection(_pay['info'], token))

    def interrupt(self):
        """
        Send an interrupt to the virtuoso shell
        """
        #self._shell.sendintr()
        #TODO: finish this
        pass

    def wait_ready(self):
        """
        Wait for the dfII to reply to the previously submitted code
        """
        self._output = self._shell.read_parsed()

    def shutdown(self, restart):
        """
        Shutdown the shell; restart if requested
        """
        if restart:
            self._shell.close()
            self._shell.init()
        else:
            self.run_raw('exit()')
            self._shell.close()
