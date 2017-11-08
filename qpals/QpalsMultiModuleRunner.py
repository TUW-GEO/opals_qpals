"""
/***************************************************************************
Name			 	 : qpalsMultiModuleRunner
Description          : Class to allow subsequental running of multiple modules asynchroneously
Date                 : 2017-11-07
copyright            : (C) 2017 by Lukas Winiwarter/GEO @ TU Wien
email                : lukas.winiwarter@geo.tuwien.ac.at
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 """


class qpalsMultiModuleRunner:
    def __init__(self):
        self.modules = []
        self.thread = None
        self.worker = None

    def add_module(self, moduleInst, status_fun, on_finish, on_error):
        self.modules.append({'module': moduleInst,
                             'status': status_fun,
                             'on_finish': on_finish,
                             'on_error': on_error,
                             'completed': False})
    def start(self):
        self.run_next_module()

    def run_next_module(self):
        for moddict in self.modules:
            if moddict['completed']:
                continue
            mod = moddict['module']
            status = moddict['status']
            err = moddict['on_error']
            fin = moddict['on_finish']
            self.thread, self.worker = mod.run_async(on_finish=fin,
                                                     on_error=err,
                                                     status=status,
                                                     run_now=False)
            self.worker.finished.connect(self.module_run_finished)
            self.thread.start()
            break

    def module_run_finished(self, ret):
        err, errm, module = ret
        for moddict in self.modules:
            if moddict['module'] is module:
                moddict['completed'] = True
        self.run_next_module()