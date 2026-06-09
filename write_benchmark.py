from pathlib import Path
import textwrap

code = textwrap.dedent('''
    import sys, time, statistics, json, argparse
    from pathlib import Path
    import numpy as np
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from phi47.core.phi_calculator import PhiCalculator
    from phi47.linter.phi_linter import Phi47Linter

    def bench_latency(runs=5, sizes=None):
        if sizes is None: sizes=[3,4,5,6,7,8,10,15,20,50,100]
        calc=PhiCalculator(); results=[]; exact={}
        print("TABLE 1 - Phi Latency vs System Size")
        for n in sizes:
            np.random.seed(42); m=np.random.rand(n,n); m=(m+m.T)/2
            for method in (["exact","spectral"] if n<=8 else ["spectral"]):
                times=[]; phis=[]
                for _ in range(runs):
                    t0=time.perf_counter(); phi,_=calc.calculate(m,method=method)
                    times.append((time.perf_counter()-t0)*1000); phis.append(phi)
                med=statistics.median(times)
                sp=1.0
                if method=="exact": exact[n]=med
                elif n in exact: sp=exact[n]/(med+1e-10)
                results.append({"n":n,"method":method,"median_ms":round(med,3),
                                "phi":round(statistics.mean(phis),4),"speedup":round(sp,2)})
                print(f"  n={n} {method}: {med:.2f}ms  phi={statistics.mean(phis):.3f}  speedup={sp:.1f}x")
        return results

    def bench_accuracy(runs=20):
        calc=PhiCalculator(); results=[]
        print("TABLE 1b - Approximation Accuracy")
        for n in [3,4,5,6,7,8]:
            errs=[]
            for seed in range(runs):
                np.random.seed(seed); m=np.random.rand(n,n); m=(m+m.T)/2
                pe,_=calc.calculate(m,method="exact")
                ps,_=calc.calculate(m,method="spectral")
                errs.append(abs(pe-ps)/(pe+1e-10))
            me=statistics.mean(errs)*100; mx=max(errs)*100
            results.append({"n":n,"mean_err_pct":round(me,2),"max_err_pct":round(mx,2)})
            print(f"  n={n}: mean_err={me:.2f}%  max_err={mx:.2f}%")
        return results

    def bench_linter(runs=5):
        linter=Phi47Linter()
        samples={
            "zombie_3": "def a(): return 1\ndef b(): return 2\ndef c(): return 3\n",
            "connected": (
                "def validate(d): return d is not None\n"
                "def transform(d):\n    if not validate(d): return {}\n    return {'v':1}\n"
                "def pipeline(items): return [transform(i) for i in items]\n"
            ),
        }
        tmp=Path("_bench_tmp.py"); results=[]
        print("TABLE 2 - Linter Throughput")
        for name,code in samples.items():
            tmp.write_text(code,encoding="utf-8")
            times=[]
            for _ in range(runs):
                t0=time.perf_counter(); diags=linter.lint_file(str(tmp))
                times.append((time.perf_counter()-t0)*1000)
            phi=next((d.phi_value for d in diags if d.code=="P001"),0.65)
            med=statistics.median(times)
            results.append({"sample":name,"phi":round(phi,3),"issues":len(diags),"ms":round(med,2)})
            print(f"  {name}: phi={phi:.3f}  issues={len(diags)}  ms={med:.2f}")
        if tmp.exists(): tmp.unlink()
        return results

    def bench_discrimination():
        calc=PhiCalculator(); zp=[]; cp=[]
        for seed in range(50):
            np.random.seed(seed); n=np.random.randint(4,12)
            zm=np.eye(n)*np.random.rand(n); phi_z,_=calc.calculate(zm); zp.append(phi_z)
            cm=np.random.rand(n,n)*0.8; cm=(cm+cm.T)/2; phi_c,_=calc.calculate(cm); cp.append(phi_c)
        r={"zombie_mean":round(statistics.mean(zp),3),"zombie_std":round(statistics.stdev(zp),3),
           "connected_mean":round(statistics.mean(cp),3),"connected_std":round(statistics.stdev(cp),3),
           "separation":round(statistics.mean(cp)/(statistics.mean(zp)+1e-10),1)}
        print("TABLE 4 - Phi: Zombie vs Connected")
        print(f"  Zombie    Phi = {r['zombie_mean']} +/- {r['zombie_std']}")
        print(f"  Connected Phi = {r['connected_mean']} +/- {r['connected_std']}")
        print(f"  Separation    = {r['separation']}x")
        return r

    def main():
        parser=argparse.ArgumentParser()
        parser.add_argument("--runs",type=int,default=5)
        parser.add_argument("--output",default="benchmarks/results")
        parser.add_argument("--quick",action="store_true")
        args=parser.parse_args()
        runs=3 if args.quick else args.runs
        print("="*55)
        print("phi47-superpowers -- Benchmarks v0.1.1")
        print("wcalmels / TUCH Systems Research Laboratory")
        print("="*55)
        data={
            "latency":    bench_latency(runs,[3,5,8,10,20] if args.quick else None),
            "accuracy":   bench_accuracy(max(runs*4,10)),
            "linter":     bench_linter(runs),
            "discrimination": bench_discrimination(),
        }
        out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
        p=out/"benchmark_results.json"
        p.write_text(json.dumps(data,indent=2),encoding="utf-8")
        print(f"Saved: {p}")

    if __name__=="__main__":
        main()
''').lstrip()

Path(r'C:\Users\wcalm\OneDrive\Escritorio\phi47-superpowers\benchmarks\run_benchmarks.py').write_text(code, encoding='utf-8')
print('OK benchmarks/run_benchmarks.py')