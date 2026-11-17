"""Native macOS login app. Profile installation remains an explicit user/MDM action."""
import os
import sys
import subprocess
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox
from macclient import read_config,environment,root_dir,helper_path


def main():
    root=tk.Tk();root.title('AWSome Gateway 로그인');root.geometry('600x420');root.resizable(False,False)
    frame=ttk.Frame(root,padding=24);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='회사 계정으로 Claude 연결',font=('',17,'bold')).pack(anchor='w')
    status=tk.StringVar(value='처음에는 [Claude 연결 설정 승인]을 진행한 뒤 회사 계정으로 로그인하세요.')
    ttk.Label(frame,textvariable=status,wraplength=550).pack(anchor='w',pady=16)
    try:config=read_config()
    except Exception as exc:
        messagebox.showerror('설치 설정 오류',str(exc));root.destroy();return
    os.environ.update(environment(config))
    ttk.Label(frame,text=config['gateway_url']).pack(anchor='w',pady=8)
    buttons=[];events=queue.Queue()
    def profile():
        if os.geteuid()==0:
            messagebox.showerror('실행 계정 확인','본인 사용자 계정으로 앱을 실행하세요.');return
        if not messagebox.askyesno('Claude 연결 설정',
            'Claude를 회사 Gateway에 연결하는 시스템 프로파일을 엽니다.\n시스템 설정에서 내용을 확인하고 승인하세요. 기존 회사 프로파일이 있으면 IT 담당자에게 먼저 문의하세요. 계속할까요?'):return
        subprocess.Popen(['open',str(root_dir()/'ClaudeGateway.mobileconfig')])
        status.set('시스템 설정 → 일반 → 기기 관리(또는 프로파일)에서 AWSome Gateway 프로파일을 승인하세요. 완료 후 회사 계정 로그인 버튼을 누르세요.')
    def begin():
        for b in buttons:b.configure(state='disabled')
        status.set('브라우저에서 회사 계정으로 로그인해 주세요. 최대 5분 동안 기다립니다.')
        def work():
            try:
                if os.geteuid()==0:raise ValueError('관리자/root가 아닌 본인 사용자 계정으로 앱을 실행하세요.')
                from gateway_cli_oidc.oidc_client import OIDCConfig,login_pkce
                login_pkce(OIDCConfig(issuer_url=config['issuer'],client_id=config['client_id'],
                    audience=config['client_id'],admin_api_url=config['admin_api_url'],redirect_port=8090),timeout_seconds=300)
                result=subprocess.run([str(helper_path())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=45)
                if result.returncode:raise ValueError('로그인은 됐지만 개인 키 발급에 실패했습니다. IT 담당자에게 문의하세요. 코드 '+str(result.returncode))
                events.put((True,'로그인과 개인 키 발급 완료! 연결 프로파일을 승인했는지 확인하고 Claude를 완전히 종료한 뒤 다시 실행하세요.'))
            except Exception as exc:events.put((False,str(exc)))
        threading.Thread(target=work,daemon=True).start()
    def logout():
        if not messagebox.askyesno('로그아웃','이 Mac의 로그인 토큰과 키 캐시를 삭제할까요? Claude도 종료하세요. 서버 키 폐기는 별도입니다.'):return
        from gateway_cli_oidc.oidc_client import clear_tokens,clear_vk_cache
        clear_tokens();clear_vk_cache();status.set('로그아웃했습니다. 즉시 차단은 관리자에게 키 폐기를 요청하세요.')
    for label,command in [('1. Claude 연결 설정 승인 (최초 한 번)',profile),('2. 회사 계정 로그인',begin),('로그아웃',logout)]:
        b=ttk.Button(frame,text=label,command=command);b.pack(fill='x',pady=6);buttons.append(b)
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
    if sys.argv[1:]==['--self-test']:
        read_config();tk.Tcl().eval('info patchlevel')
    else:main()
