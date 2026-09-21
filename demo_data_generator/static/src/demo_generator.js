/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const CIRCUMFERENCE = 2 * Math.PI * 52;
const NON_RECORD_STEPS = ["modules", "publish_website"];

export class DemoGeneratorAction extends Component {
    static template = "demo_data_generator.Action";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.state = useState(this.initialState());
    }

    initialState() {
        return {
            phase: "idle", // idle | running | complete
            steps: [],
            done: 0,
            errors: 0,
            records: 0,
            current: "",
            working: false,
            log: [], // newest first: {key, label, detail, ok}
            fatal: "",
        };
    }

    get circumference() {
        return CIRCUMFERENCE;
    }

    get isFinished() {
        return this.state.phase === "complete" && !this.state.fatal;
    }

    get pct() {
        if (this.isFinished) {
            return 100;
        }
        const total = this.state.steps.length || 1;
        return Math.round((this.state.done / total) * 100);
    }

    get ringOffset() {
        return CIRCUMFERENCE - (this.pct / 100) * CIRCUMFERENCE;
    }

    get currentClass() {
        const s = this.state;
        if (s.phase === "complete") {
            return s.errors || s.fatal ? "has-errors" : "complete";
        }
        return s.working ? "working" : "";
    }

    get summary() {
        const s = this.state;
        return s.errors
            ? `Done - ${s.records} records created, ${s.errors} error(s)`
            : `Done - ${s.records} records created`;
    }

    reset() {
        Object.assign(this.state, this.initialState());
    }

    async generate() {
        this.reset();
        this.state.phase = "running";
        this.state.current = "Connecting...";
        try {
            this.state.steps = await this.orm.call("demo.data.generator", "get_steps");
            for (const step of this.state.steps) {
                this.state.current = step.label;
                this.state.working = true;
                const res = await this.orm.call("demo.data.generator", "run_step", [step.key]);
                this.state.working = false;
                this.state.done++;
                const ok = res.status === "done";
                if (!ok) {
                    this.state.errors++;
                } else if (!NON_RECORD_STEPS.includes(step.key)) {
                    this.state.records += res.count || 0;
                }
                this.state.log.unshift({
                    key: step.key,
                    label: step.label,
                    detail: res.detail || "",
                    ok,
                });
            }
            this.state.phase = "complete";
            this.state.current = this.summary;
        } catch (e) {
            this.state.working = false;
            this.state.fatal = `Connection failed: ${e.message || e}`;
            this.state.phase = "complete";
        }
    }
}

registry.category("actions").add("demo_data_generator", DemoGeneratorAction);
