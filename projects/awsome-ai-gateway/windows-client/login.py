"""Simple user-account GUI; credentials are entered only in Cognito's browser."""
import os
import sys
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox
from clientlib import read_config, environment, root_dir


def main():
    root=tk.Tk();root.title('AWSome Gateway 로그인');root.geometry('560x330');root.resizable(False,False)
    frame=ttk.Frame(root,padding=24);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='회사 계정으로 Claude 연결',font=('',17,'bold')).pack(anchor='w')
    status=tk.StringVar(value='로그인 버튼을 누르고 브라우저에서 회사 계정으로 로그인하세요.')
    ttk.Label(frame,textvariable=status,wraplength=510).pack(anchor='w',pady=18)
    try:config=read_config()
    except Exception as exc:
        messagebox.showerror('설치 설정 오류',str(exc));root.destroy();return
    os.environ.update(environment(config))
    ttk.Label(frame,text=config['gateway_url']).pack(anchor='w',pady=8)
    events=queue.Queue();buttons=[]
    def begin():
        for b in buttons:b.configure(state='disabled')
        status.set('브라우저에서 로그인해 주세요. 최대 5분 동안 기다립니다.')
        def worker():
            try:
                import ctypes
                if ctypes.windll.shell32.IsUserAnAdmin():
                    raise ValueError('로그인 앱은 관리자 권한이 아닌 평소 사용자 계정으로 실행하세요.')
                from gateway_cli_oidc.oidc_client import OIDCConfig,login_pkce
                login_pkce(OIDCConfig(issuer_url=config['issuer'],client_id=config['client_id'],
                    audience=config['client_id'],admin_api_url=config['admin_api_url'],redirect_port=8090),timeout_seconds=300)
                result=subprocess.run([str(root_dir()/'helper/api-key-helper.exe')],
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                    timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode:raise ValueError('로그인은 됐지만 키 발급이 실패했습니다. IT 담당자에게 문의하세요. 코드 '+str(result.returncode))
                events.put((True,'연결 완료! Claude를 완전히 종료한 뒤 다시 실행하고 Haiku 모델로 대화해 보세요.'))
            except Exception as exc:events.put((False,str(exc)))
        threading.Thread(target=worker,daemon=True).start()
    def logout():
        if not messagebox.askyesno('로그아웃','이 PC의 로그인 토큰과 키 캐시를 지울까요? Claude도 종료하세요. 서버 키 폐기는 별도입니다.'):return
        from gateway_cli_oidc.oidc_client import clear_tokens,clear_vk_cache
        clear_tokens();clear_vk_cache();status.set('로그아웃했습니다. 즉시 차단은 관리자에게 키 폐기를 요청하세요.')
    for text,command in [('회사 계정 로그인',begin),('로그아웃',logout)]:
        b=ttk.Button(frame,text=text,command=command);b.pack(fill='x',pady=6);buttons.append(b)
    def poll():
        try:ok,text=events.get_nowait()
        except queue.Empty:pass
        else:
            for b in buttons:b.configure(state='normal')
            status.set(text)
            if not ok:messagebox.showerror('연결 오류',text)
        root.after(150,poll)
    poll();root.mainloop()


if __name__=='__main__':
    if sys.stdout is None:sys.stdout=open(os.devnull,'w')
    if sys.stderr is None:sys.stderr=open(os.devnull,'w')
    if sys.argv[1:] == ['--self-test']:
        read_config()
        tk.Tcl().eval('info patchlevel')
    else:
        main()
